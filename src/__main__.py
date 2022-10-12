import os, sys
import logging
import json
from pprint import pprint
import  boto3
from utils.Gitlab import Gitlab
from utils.Aws import Aws
from utils.Docker import Docker

format = '%(asctime)s %(levelname)s:%(message)s'
logging.basicConfig(
    filename=os.getenv('LOG_FILE'),
    format=format,
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filemode='w',
    level=logging.DEBUG
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter(format)
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logging.info('Hi there!')
logging.info('You are going to migrate container registries from gitlab to AWS ECR')
logging.info('Here a list of the relevant repositories, ready for migration:')

g = Gitlab(logging)

for p in g.get_repo_names_to_migrate():
    logging.info(f"\t- {p}")

logging.info('AWS ECR creation:',g.get_repo_names_to_migrate())

aws = Aws(logging)
for p in g.get_repo_names_to_migrate():
    logging.info(f'Creating {p}...')
    stackname = aws.create_ecr(p)
    logging.info(f'Stack name: {stackname} and wait...')
    aws.wait_for_stack_ok(stackname)

d = Docker(logging)

gitlab_images = g.get_all_images_to_migrate()

print("gitlab_images",gitlab_images)

for gitlab_image in gitlab_images:
    logging.info('Go migrate this image '+gitlab_image['location'])
    d.migrate_image_from_gitlab_to_ecr(gitlab_image)

logging.info('Migration finished!'+"\n")

f = open("/etc/hostname","r")
container_id = f.read().strip()
logging.info('You can get the log file executing this command from host:'+"\n")
logging.info('docker cp '+container_id+':'+os.getenv('LOG_FILE'))