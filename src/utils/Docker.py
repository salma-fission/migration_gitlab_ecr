import logging
import os, sys, base64, subprocess
from pprint import pprint
from re import sub
import docker
import boto3


class Docker:
    
    def __init__(self, logger) -> None:
        self._logger = logger
    
    def login_gitlab(self):
        client = docker.from_env()
        r = client.login(username=os.getenv('GITLAB_USERNAME'), password=os.getenv('GITLAB_PERSONAL_TOKEN'),
                       registry=os.getenv('GITLAB_HOST'))

        self._logger.info(r)

        return client

    def login_ecr(self):
        client = docker.from_env()
        ecr = boto3.client('ecr', region_name=os.getenv('AWS_DEFAULT_REGION'),aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
         aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))
        token = ecr.get_authorization_token()
        username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
        registry = token['authorizationData'][0]['proxyEndpoint']
        r = client.login(username, password, registry=registry)

        self._logger.info(r)

        return client

    def migrate_image_from_gitlab_to_ecr(self, gitlab_image):
        repoName = gitlab_image['path'].split(':')[0]
        tag = gitlab_image['name']
        digestFromGitlab = gitlab_image['digest_from_gitlab']

        ecr = boto3.client('ecr', region_name=os.getenv('AWS_DEFAULT_REGION'),aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
         aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))

        # Check if image is already in ECR
        r = ecr.batch_get_image(repositoryName=repoName, imageIds=[{'imageTag': tag}])

        if r['images'] and r['images'][0]['imageId']['imageDigest']:
            digestFromECR = r['images'][0]['imageId']['imageDigest']
            if digestFromGitlab and (str(digestFromECR) == str(digestFromGitlab)):
                self._logger.info('Nothing to do because digestFromECR == digestFromGitlab')
                self._logger.info(digestFromECR+' == '+digestFromGitlab)

                return # Bye

        # Login to Gitlab
        cmd = 'docker login '+os.getenv('GITLAB_DOCKER_HOST')+' -u '+os.getenv('GITLAB_USERNAME')+' -p '+os.getenv('GITLAB_PERSONAL_TOKEN')
        self.__run_command(cmd)

        # Pull image from Gitlab
        cmd = 'docker pull '+gitlab_image['location']
        self.__run_command(cmd)

        r = ecr.describe_repositories(repositoryNames=[repoName])
        ecr_uri = r['repositories'][0]['repositoryUri']
        ecr_image_url = ecr_uri+':'+tag

        # Tag image with ecr
        cmd = 'docker tag '+gitlab_image['location']+' '+ecr_image_url
        self.__run_command(cmd)
        
        # Login to AWS ECR
        cmd = 'aws ecr get-login-password --region '+os.getenv('AWS_DEFAULT_REGION')+' | docker login --username AWS --password-stdin '+ecr_uri
        self.__run_command(cmd)

        # Push image to AWS ECR
        cmd = 'docker push '+ecr_image_url
        self.__run_command(cmd)

        # Purge everything locally
        cmd = 'docker system prune --all --force'
        self.__run_command(cmd)
        
    def __run_command(self, cmd):
        self._logger.info(cmd)
        r = subprocess.run([cmd], shell=True, capture_output=True, text=True)
        if r.stderr:
            self._logger.error(r.stderr)
        if r.stdout:
            self._logger.info(r.stdout)
