import os
import subprocess
import boto3
import yaml
from bitbucket_pipes_toolkit import Pipe, get_logger

logger = get_logger()

# Define the schema for the pipe
schema = {
    'AWS_DEFAULT_REGION': {'type': 'string', 'required': True},
    'AWS_ROLE_ARN': {'type': 'string', 'required': True},
    'AWS_ROLE_SESSION_NAME': {'type': 'string', 'required': True},
    'AWS_ENVIRONMENT': {'type': 'string', 'required': True},
    'AWS_VPC_ID': {'type': 'string', 'required': True},
    'AWS_SUBNET_ID': {'type': 'string', 'required': True},
    'AWS_SECURITY_GROUP_ID': {'type': 'string', 'required': True},
    'AWS_PARAMETER_STORE_NAME': {'type': 'string', 'required': True},
    'PACKER_SOURCE_NAME': {'type': 'string', 'required': True},
    'PACKER_BUILD_FILE': {'type': 'string', 'required': True},
    'AWS_PARAMETER_UPDATE_FILENAME' : {'type': 'string', 'required': True},
}


class PackerBuild(Pipe):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load AWS and Packer environment variables
        self.aws_default_region = os.getenv('AWS_DEFAULT_REGION')
        self.aws_oidc_role = os.getenv('AWS_ROLE_ARN')
        self.aws_oidc_role_name = os.getenv('AWS_ROLE_SESSION_NAME')
        self.aws_environment = os.getenv('AWS_ENVIRONMENT')
        self.aws_vpc_id = os.getenv('AWS_VPC_ID')
        self.aws_security_group_id = os.getenv('AWS_SECURITY_GROUP_ID')
        self.aws_subnet_id = os.getenv('AWS_SUBNET_ID')
        self.aws_parameter_store_name = os.getenv('AWS_PARAMETER_STORE_NAME')
        self.packer_source_name = os.getenv('PACKER_SOURCE_NAME')
        self.packer_build_file = os.getenv('PACKER_BUILD_FILE')
        self.aws_parameter_update_filename = os.getenv('AWS_PARAMETER_UPDATE_FILENAME')
        self.config = self.get_variable('CONFIG')

    def setup_aws_env_credentials(self):
        """Set up AWS environment credentials by assuming the provided role using OIDC."""
        self.log_info("Assuming provided AWS OIDC role with the web-identity")
        # Fetch the Web Identity Token from environment variables
        web_identity_token = os.getenv('BITBUCKET_STEP_OIDC_TOKEN')
        if not web_identity_token:
            self.log_error('Web identity token not found in environment variables.')
            raise ValueError('Web identity token is required for OIDC authentication.')

        # Create an STS client and assume the role using web identity
        client = boto3.client('sts')
        response = client.assume_role_with_web_identity(
            RoleArn=self.aws_oidc_role,
            RoleSessionName=self.aws_oidc_role_name,
            WebIdentityToken=web_identity_token #Getting the Bitbucket Step OIDC Token
        )

        # Set the assumed role credentials into the environment
        os.environ['AWS_ACCESS_KEY_ID'] = response['Credentials']['AccessKeyId']
        os.environ['AWS_SECRET_ACCESS_KEY'] = response['Credentials']['SecretAccessKey']
        os.environ['AWS_SESSION_TOKEN'] = response['Credentials']['SessionToken']
        self.log_info("Set up temporary AWS credentials in the environment")

    def run_packer_build(self):
        """Run the Packer build process."""
        self.log_info(f"Running Packer build with source name: {self.packer_source_name}")

        # Run packer init .
        init_command = ["packer", "init", self.packer_build_file]
        build_command = [
            "packer", "build",
            "-var", f"env={self.aws_environment}",
            "-var", f"vpcid={self.aws_vpc_id}",
            "-var", f"source_name={self.packer_source_name}",
            "-var", f"subnetid={self.aws_subnet_id}",
            "-var", f"securitygroupid={self.aws_security_group_id}",
            "-var", f"parameterstore={ self.aws_parameter_store_name}",
            "-var", f"parameterupdatefile={self.aws_parameter_update_filename}",
            self.packer_build_file
        ]
        try:
            self.log_info("Running packer init command")
            init_result = subprocess.run(init_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.log_info(f"Packer init output: {init_result.stdout.decode('utf-8')}")
        except subprocess.CalledProcessError as e:
            self.log_error(f"Packer init failed: {e.stderr.decode('utf-8')}")
            raise
        try:
            self.log_info("Running packer build command")
            build_result = subprocess.Popen(build_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in build_result.stdout:
                self.log_info(line.strip())
            build_result.wait()
            if build_result.returncode != 0: #If the return code is not 0, raise an exception
                raise subprocess.CalledProcessError(build_result.returncode, build_command)
        except subprocess.CalledProcessError as e:
            self.log_error(f"Packer build failed: {e.stderr.decode('utf-8')}")
            if e.stderr:
                error_message += f": {e.stderr.decode('utf-8')}"
            else:
                error_message += ": No additional error information available."
            self.log_error(error_message)
            raise
        
    def run(self):
        """Run the Packer build pipeline."""
        # Set up AWS credentials
        self.setup_aws_env_credentials()
        # Execute the Packer build
        self.run_packer_build()

if __name__ == '__main__':
    with open('/pipe.yml', 'r') as metadata_file:
        metadata = yaml.safe_load(metadata_file.read())
        pipe = PackerBuild(schema=schema, pipe_metadata=metadata, check_for_newer_version=True)
        pipe.run()
