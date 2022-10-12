import os, sys, time
import boto3
import requests
from slugify import slugify
from pprint import pprint



class Aws():

    def __init__(self, logger) -> None:
        self.session = boto3.session.Session()
        self._logger = logger

    def create_ecr(self, name) -> str:
        stackname = slugify('a'+name.lower() + '-ecr-stack')
        cf_template = open('src\iac\ecr.yml').read()
        client = boto3.client('cloudformation', region_name=os.getenv('AWS_DEFAULT_REGION'),aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
         aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))

        try:
            client.create_stack(
                StackName=stackname,
                TemplateBody=cf_template,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Parameters=[
                    {
                        'ParameterKey': 'repoName',
                        'ParameterValue': name.lower()
                    }
                ]
            )
        except client.exceptions.AlreadyExistsException as e:
            self._logger.warning(f'{stackname} is already there!')

        return stackname

    def wait_for_stack_ok(self, stackname):
        
        while self.__get_stack_status(stackname) != 'CREATE_COMPLETE':
            time.sleep(2)
            self._logger.info('.')

            if self.__get_stack_status(stackname) in ['CREATE_FAILED', 'ROLLBACK_IN_PROGRESS', 'ROLLBACK_COMPLETE']:
                self._logger.error(stackname+' failed during creation')
                raise Exception(stackname+' failed during creation')

    def test(self) -> list:
        client = boto3.client('s3', region_name=os.getenv('AWS_DEFAULT_REGION'),aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
         aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))
        response = client.list_buckets()
        return response

    def __get_stack_status(self, stackname):
        client = boto3.client('cloudformation', region_name=os.getenv('AWS_DEFAULT_REGION'),aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
         aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))
        r = client.describe_stacks(StackName=stackname)
    
        for stack in r['Stacks']:
            if str(stack['StackName']) == stackname:
                return stack['StackStatus']
