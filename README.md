# Gitlab to AWS ECR migration
The purpose here is to migrate images and tags from a Gitlab registry to the AWS Elastic Container Registry service
## Configuration
Create `.env` file from the sample
```
cp .env.sample .env
```
Set your own config and crednetials

## Build and Run
**IMPORTANT**: You can run the migration **more than once** without danger, it will not recreate already created repositories or not migrate already migrated images
 - Note that you need to share docker.sock from the host
```
docker build -t gitlab-to-ecr . 

docker run --env-file ./.env -v /var/run/docker.sock:/var/run/docker.sock gitlab-to-ecr
```
To run the migration in a detached mode, simply add a `-d` after `docker run `.

### Get the log file when migration ended
```
docker ps -a
```
Get the `<CONTAINER ID>`, a string like `9cdea71a7026`, take the one with `IMAGE` named `gitlab-to-ecr` and then copy the file from the container to the host:
```
docker cp <CONTAINER ID>:/var/log/gitlab-to-ecr.log .
```

## Launch from EC2 Amazon Linux
1. Create the instance from AWS console with a 20GB disk space
2. ssh to it and...
```
sudo yum update
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo chkconfig docker on
sudo yum install -y git
sudo reboot
```
3. ssh again, git clone, docker build and docker run (see up)

## Change ECR configuration after the first run
Only change ECR configuration within CloudFormation stacks (console, aws cli or SDK) to keep consistency and track changes. See inside `iac/`.

## Troubleshooting
 - Note that you'll need to have a read-only token from Gitlab (no sudo).