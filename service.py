#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

BASE_URL = 'http://coca.localhost'


class ServiceException(Exception):
    pass


def get_all_classes(modified_since=None):
    url = BASE_URL + '/sku/list'
    try:
        response = requests.get(url, {'modifiedSince': modified_since})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if response.ok:
        data = response.json()
        return data['skus'], data['lastModifyTime']
    else:
        error = response.json()
        raise ServiceException(error['message'])


def add_class(class_name):
    url = BASE_URL + '/sku/create'
    try:
        response = requests.post(url, {'name': class_name})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if response.ok:
        return response.json()
    else:
        error = response.json()
        raise ServiceException(error['message'])


def remove_class(class_name):
    url = BASE_URL + '/sku/delete'
    try:
        response = requests.post(url, {'name': class_name})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if response.ok:
        return response.json()
    else:
        error = response.json()
        raise ServiceException(error['message'])

if __name__ == '__main__':
    print get_all_classes()
