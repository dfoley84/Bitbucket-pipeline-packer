# bitbucket-packer

This Bitbucket pipe assumes an AWS role using OpenID Connect (OIDC) and runs a Packer build that provisions infrastructure based on provided environment variables, including AWS VPC, Subnet, Security Group, and AWS Systems Manager (SSM) Parameter Store details.

Code Overview
The pipe has two key functionalities:

AWS OIDC Role Authentication:

Uses Bitbucket OIDC to assume an AWS role via sts:AssumeRoleWithWebIdentity.
Packer Build Execution:

Runs Packer commands to initialize and build infrastructure using environment variables such as VPC ID, Subnet ID, and Security Group ID.
YAML Definition
Include this pipe in your bitbucket-pipelines.yml file and define the required environment variables:

```yaml
 steps:
    - step: &Packer
        name: 'Packer Build'
        oidc: true
        script:   
          - pipe: docker://davefoley/bitbucket-packer:latest
            variables:
              AWS_DEFAULT_REGION: "<string>"
              AWS_ROLE_ARN: "<string>"
              AWS_ROLE_SESSION_NAME: "<string>"
              AWS_ENVIRONMENT: "<string>"
              AWS_VPC_ID: "<string>"
              PACKER_SOURCE_NAME: "<string>"
              AWS_SUBNET_ID: "<string>"
              AWS_SECURITY_GROUP_ID: "<string>"
              AWS_PARAMETER_STORE_NAME: "<string>"
              AWS_PARAMETER_UPDATE_FILENAME: "<string>"
```


## Variables

| Variable                          | Usage                                                                                                                                          |
|-----------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| AWS_DEFAULT_REGION (*)                 | AWS region to execute the Packer build. Example: eu-west-1..                                                                                                                 |
| AWS_ROLE_ARN (*)                   | he AWS IAM role ARN to assume. Required for OIDC authentication                                      |
| AWS_ROLE_SESSION_NAME (*)                   | Session name for the assumed AWS role.                                          |
| AWS_ENVIRONMENT (*)               | Name of the environment (e.g., staging, production). |
| AWS_VPC_ID (*) | 	The VPC ID where the infrastructure will be deployed..                                                                     |
| AWS_SUBNET_ID (*)                   | The Subnet ID to be used for provisioning infrastructure.
| AWS_SECURITY_GROUP_ID (*)                   | The Security Group ID associated with the infrastructure.  |
| AWS_PARAMETER_STORE_NAME (*)                   | The name of the AWS Systems Manager Parameter Store parameter to retrieve.  |
| PACKER_SOURCE_NAME (*)                 | The name of the file containing updates for AWS SSM Parameter Store.  |
| AWS_PARAMETER_UPDATE_FILENAME (*)                  | The Security Group ID associated with the infrastructure.  |
| BITBUCKET_STEP_OIDC_TOKEN (*)                             | 	Bitbucket OIDC token (automatically injected by Bitbucket in OIDC-enabled steps).                                                                                             |

_(*) = required variable._


### Key Functions
1. setup_aws_env_credentials()
Assumes the AWS IAM role using Bitbucket's OIDC token.
Fetches the token from the BITBUCKET_STEP_OIDC_TOKEN environment variable.
Uses AWS STS to obtain temporary AWS credentials (Access Key ID, Secret Access Key, and Session Token) and sets them in the environment.
2. run_packer_build()
Initializes the Packer configuration and executes the Packer build.

Uses the environment variables provided (such as VPC ID, Subnet ID, Security Group ID, and AWS SSM Parameter) in the build process.


### Commands:

packer init: Initializes the Packer template.
packer build: Runs the Packer build with the environment variables passed as -var arguments.
3. Error Handling
Captures any errors from the Packer commands and logs them for troubleshooting.
Logging
The pipe uses bitbucket_pipes_toolkit for structured logging, helping you easily identify issues with AWS credential setup or the Packer build process.