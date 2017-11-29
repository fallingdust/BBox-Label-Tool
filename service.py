#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests

# BASE_URL = 'http://annotation.localhost'
BASE_URL = 'http://111.231.50.154:8888'
# BASE_URL = 'http://ubuntu.zhixiang.co:8888'


class ServiceException(Exception):
    pass


def get_all_images():
    url = BASE_URL + '/image/list'
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.json()
    else:
        error = r.json()
        raise ServiceException(error['message'])


def load_image(filename):
    url = BASE_URL + '/image/view'
    try:
        r = requests.get(url, {'file': filename}, stream=True)
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.raw
    else:
        raise ServiceException('Load image failed')


def get_all_classes():
    url = BASE_URL + '/sku/list'
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.json()
    else:
        error = r.json()
        raise ServiceException(error['message'])


def get_detection(image):
    url = BASE_URL + '/detection/view'
    try:
        r = requests.get(url, {'image_file': image})
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return r.json()
    elif r.status_code == 404:
        return None
    else:
        error = r.json()
        raise ServiceException(error['message'])


def save_detection(detection):
    url = BASE_URL + '/detection/update'
    try:
        r = requests.post(url, None, detection)
    except requests.exceptions.RequestException:
        raise ServiceException('Network communication error')
    if r.ok:
        return True
    else:
        error = r.json()
        raise ServiceException(error['message'])


if __name__ == '__main__':
    print get_all_classes()
