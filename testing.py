# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 21:17:20 2017

@author: jaime
"""
domain = 'https://icifacial.com/'
url = 'https://icifacial.com/rinoplastia/cirugia de nariz'
part = str(url.split(domain)[1]).split('/')[0]
print(part)