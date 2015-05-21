#!/usr/bin/python
from XmlParse import XmlParse, XmlParseTest
import unittest

# создаём экземпляр класса
xml = XmlParse()
file = './XmlParseTest/source.xml'
xml.parent_tag = 'input'
xml.parent_attr = 'id'
xml.child_tag = 'tuningSetup'
xml.child_attr = 'id'

# разбираем предоставленный в тестовом задании XML документ
print ('Разбираем ' + file + ', результат: \n') 
print (xml.parse(file))