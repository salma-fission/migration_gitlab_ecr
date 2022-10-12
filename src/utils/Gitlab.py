import logging
import os, sys
import re
import requests
from pprint import pp, pprint
import docker

from decouple import config


class Gitlab:

    req_headers = {'PRIVATE-TOKEN': config('GITLAB_PERSONAL_TOKEN')}
    req_url = config('GITLAB_HOST')+config('GITLAB_URL_PREFIX')

    def __init__(self, logger) -> None:
        self._logger = logger
        pass

    def get_repo_names_to_migrate(self) -> list:
        registries = self.__get_all_projects_with_registry()

        res = []

        for repos in registries:
            for repo in repos:
                path = repo['path']
                res.append(path)

        return res
    
    def get_repo_ids_to_migrate(self) -> list:
        registries = self.__get_all_projects_with_registry()

        res = []

        for registry in registries:
            res.append(registry[0]['project_id'])

        return res
        
    def get_all_images_to_migrate(self):
        repo_ids = self.get_repo_ids_to_migrate()
        #repo_ids = [11] # TODO REMOVE ME, JUST FOR TESTING
        res = []
        for repo_id in repo_ids:
            url = f"{self.req_url}/projects/{repo_id}/registry/repositories?tags=true"
            r = requests.get(url, headers=self.req_headers)
            r = r.json()

            for repo in r:
                tags = repo['tags']
                for tag in tags:
                    tag['repository_id'] = repo['id']
                    tag['project_id'] = repo['project_id']
                    tag['digest_from_gitlab'] = self.__get_digest_from_tag(
                        tag['project_id'], 
                        tag['repository_id'], 
                        tag['name'])
                    res.append(tag)

        return res
            
    def __get_digest_from_tag(self, project_id, repository_id, tag):
        url = f"{self.req_url}/projects/{project_id}/registry/repositories/{repository_id}/tags/{tag}"
        r = requests.get(url, headers=self.req_headers)
        return r.json()['digest']
    
    def __get_project_by_id(self, id):
        url = f"{self.req_url}/projects/{id}"
        r = requests.get(url, headers=self.req_headers)
        return r.json()

    def __get_all_projects(self) -> list:
        url = f"{self.req_url}/projects"
        r = requests.get(url, headers=self.req_headers)
        return r.json()

    def __get_all_projects_with_registry(self) -> list:
        projects = self.__get_all_projects()

        res = []
        # for project in projects:
           
        # id = project['id']
        url = f"{self.req_url}/projects/35680660/registry/repositories"
        r = requests.get(url, headers=self.req_headers)
        print("reo",r.json())
        if len(r.json()) > 0:
            res.append(r.json())
        print("repo",res)   
        return res

    
