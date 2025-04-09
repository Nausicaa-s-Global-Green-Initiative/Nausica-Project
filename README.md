# Nausica-Project

## Deploy Flask to AWS Elastic Beanstalk with GitHub Actions

The GitHub Actions workflow automates the deployment of a Flask application to AWS Elastic Beanstalk whenever changes are pushed to the dev branch or a pull request is opened against dev.

Prerequisites

Before using this CI/CD pipeline, ensure you have the following:

An AWS Elastic Beanstalk environment set up (if not already done).

GitHub Secrets configured for authentication and deployment:

AWS_ACCESS_KEY_ID

AWS_SECRET_ACCESS_KEY

AWS_REGION

EB_APPLICATION_NAME

EB_ENVIRONMENT_NAME

DB_USER

DB_PASSWORD

DB_HOST

DB_NAME

DB_PORT

Workflow Overview

The GitHub Actions workflow performs the following steps:

1. Trigger Conditions

Runs when a push occurs on the dev branch.

Runs when a pull request targets the dev branch.

2. Job: Deploy Flask App

Runs on ubuntu-latest and executes the following steps:

Checkout Repository

- name: Checkout Repository
  uses: actions/checkout@v4

Clones the repository to the runner machine.

Set up Python

- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: "3.9"

Installs Python 3.9, required for the Flask application and AWS Elastic Beanstalk.

Install Dependencies

- name: Install Dependencies
  run: |
    pip install -r nausica-grant-application/requirements.txt

Installs the required Python dependencies listed in requirements.txt.

Package Application

- name: Package Application
  run: zip -r deploy.zip . -x "venv/*" ".git/*" ".github/*"

Creates a deployment package, excluding unnecessary files such as virtual environments and Git metadata.

Install AWS CLI & Elastic Beanstalk CLI

- name: Install AWS CLI & Elastic Beanstalk CLI
  run: |
    python -m pip install --upgrade pip
    pip install awscli
    pip install awsebcli
    pip install --upgrade awscli botocore

Installs AWS CLI and Elastic Beanstalk CLI for managing deployments.

Configure AWS CLI

- name: Configure AWS CLI
  run: |
    aws configure set aws_access_key_id ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws configure set aws_secret_access_key ${{ secrets.AWS_SECRET_ACCESS_KEY }}

Configures AWS CLI using credentials stored in GitHub Secrets.

Deploy to Elastic Beanstalk

- name: Deploy to Elastic Beanstalk
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_REGION: ${{ secrets.AWS_REGION }}
    EB_APPLICATION_NAME: ${{ secrets.EB_APPLICATION_NAME }}
    EB_ENVIRONMENT_NAME: ${{ secrets.EB_ENVIRONMENT_NAME }}
    DB_USER: ${{ secrets.DB_USER }}
    DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
    DB_HOST: ${{ secrets.DB_HOST }}
    DB_NAME: ${{ secrets.DB_NAME }}
    DB_PORT: ${{ secrets.DB_PORT }}
  run: |
    env | grep DB_
    eb init "$EB_APPLICATION_NAME" --region "$AWS_REGION" --platform "Python 3.9"
    eb deploy "$EB_ENVIRONMENT_NAME"

Initialises the Elastic Beanstalk environment and deploys the application.

How to Use

Ensure the required AWS resources are set up.

Push changes to the dev branch or open a pull request targeting dev.

GitHub Actions will automatically execute the deployment process.

Monitor the workflow logs in GitHub Actions for any issues.

Troubleshooting

If deployment fails, check the GitHub Actions logs for errors or check elastic beanstalk logs for deployment errors.

Verify AWS credentials in GitHub Secrets.

Ensure that requirements.txt includes all necessary dependencies.

Make sure the correct AWS region, application name, and environment name are set.
