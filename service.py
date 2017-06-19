#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

# BASE_URL = 'http://coca.localhost'
BASE_URL = 'http://ubuntu.zhixiang.co:8080'


class ServiceException(Exception):
    pass


def get_all_classes(modified_since=None):
    url = BASE_URL + '/sku/list'
    try:
        r = requests.get(url, {'modifiedSince': modified_since})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        data = r.json()
        return data['skus'], data['lastModifyTime']
    else:
        error = r.json()
        raise ServiceException(error['message'])


def add_class(class_name):
    url = BASE_URL + '/sku/create'
    try:
        r = requests.post(url, {'name': class_name})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.json()
    else:
        error = r.json()
        raise ServiceException(error['message'])


def remove_class(class_name):
    url = BASE_URL + '/sku/delete'
    try:
        r = requests.post(url, {'name': class_name})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.json()
    else:
        error = r.json()
        raise ServiceException(error['message'])


def get_annotation(image):
    url = BASE_URL + '/annotation/view'
    try:
        r = requests.get(url, {'image': image})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.json()
    elif r.status_code == 404:
        return None
    else:
        error = r.json()
        raise ServiceException(error['message'])


def save_annotation(annotation):
    url = BASE_URL + '/annotation/upsert'
    try:
        r = requests.post(url, None, annotation)
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return True
    else:
        error = r.json()
        raise ServiceException(error['message'])

if __name__ == '__main__':
    print get_all_classes()
