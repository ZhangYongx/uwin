# -*- coding: utf-8 -*-

import commands
import os, sys
import json
import time
import hmac
import hashlib
import base64
import requests
import os
import sys
import logging
import traceback
import subprocess

open_api_ip = '10.253.68.20'
cmdb_ip = '10.253.68.20'
open_api_host = 'openapi.easyops-only.com'

ACCESS_KEY = ''
SECRET_KEY = ''


def get_the_key():
	cmdb_api_url = 'http://%s/profile/apikey' % cmdb_ip
	headers = {'org': 1021, 'user': 'deppon', 'Host': 'cmdb.easyops-only.com'}
	resp = requests.get(cmdb_api_url, headers=headers)

	data = {}
	if resp.status_code == 200:
		data = resp.json()

	print data
	ACCESS_KEY = data.get('data').get('access_key')
	SECRET_KEY = data.get('data').get('secret_key')

	return ACCESS_KEY, SECRET_KEY


def open_api_requests(method, url, data, headers):
	if method == 'GET':
		resp = requests.get(url, params=data, headers=headers)
	elif method == 'POST':
		resp = requests.post(url, data=data, headers=headers)

	if resp.status_code == 200:
		return resp.json()

	return {}


def generate_signature(method, uri, params, content_type, data, request_time, access_key, secret_key):
	method = method.upper()
	# 对 params 进排序, 然后组合为一串 key + value 的string
	params_str = ''

	if method == 'GET' and params:
		params_str = ''.join(['%s%s' % (key, params[key]) for key in sorted(params.keys())])

	# Content-MD5
	content_md5 = ''
	if method == 'POST' and data:
		m = hashlib.md5()
		m.update(json.dumps(data).encode('utf-8'))
		content_md5 = m.hexdigest()

	# 组合 str
	str_sign = str('\n'.join([
		method,
		uri,
		params_str,
		content_type,
		content_md5,
		str(request_time),
		access_key
	]))

	# print type(str_sign)
	# print str_sign
	signature = hmac.new(str(secret_key), str_sign, hashlib.sha1).hexdigest()

	return signature


def do_api_with_openapi(method, uri, access_key, secret_key, data={}):
	url = 'http://{0}{1}'.format(open_api_ip, uri)
	headers = {
		'Host': open_api_host,
		'Content-Type': 'application/x-www-form-urlencoded'
	}

	request_time = int(time.time())
	signature = generate_signature(method=method,
	                               uri=uri,
	                               params=data,
	                               content_type=headers.get('Content-Type'),
	                               data=data,
	                               request_time=str(request_time),
	                               access_key=access_key,
	                               secret_key=secret_key)

	# print signature
	data.update({
		"accesskey": access_key,
		"signature": signature,
		"expires": str(request_time)
	})

	return open_api_requests(method, url, data, headers)


def get_monitor_info(paras={}):
	uri = '/cmdb/object/instance/list/monitor'  # 请求监控管理对象
	params = {}

	for key, value in paras.iteritems():
		if not value:
			continue

		params['%s' % key] = base64.b64encode(value.encode('utf-8'))

	data = do_api_with_openapi(method='GET',
	                           uri=uri,
	                           access_key=ACCESS_KEY,
	                           secret_key=SECRET_KEY,
	                           data=params)

	records = data.get('data', {}).get('list', [])
	groups = []
	users = []
	for rec in records:
		res = rec.get('msguser') or []
		for user in res:
			users.append({
				'name': user['name'],
				'user_tel': user['user_tel'],
				'user_email': user['user_email'],
				'user_stuffid': user['user_stuffid'],
			})

		if rec.get('msggroup'):
			groups += [item['name'] for item in rec.get('msggroup') if item['name']]

	groups = list(set(groups))
	return users, groups


def get_group_info(group_names):
	uri = '/cmdb/object/instance/list/usergroup'
	params = {
		'name': ','.join([base64.b64encode(name.encode('utf-8')) for name in group_names])
	}

	data = do_api_with_openapi(method='GET',
	                           uri=uri,
	                           access_key=ACCESS_KEY,
	                           secret_key=SECRET_KEY,
	                           data=params)

	records = data.get('data', {}).get('list', [])
	users = []
	for rec in records:
		result = rec.get('users', [])
		for user in result:
			users.append({
				'name': user['name'],
				'user_tel': user['user_tel'],
				'user_email': user['user_email'],
				'user_stuffid': user['user_stuffid']
			})

	return users


def user_api(param):
	uri = '/cmdb/object/instance/list/USER'
	params = {
		'name$in': ','.join([base64.b64encode(name.encode('utf-8')) for name in param])
	}

	data = do_api_with_openapi(method='GET',
	                           uri=uri,
	                           access_key=ACCESS_KEY,
	                           secret_key=SECRET_KEY,
	                           data=params)

	print data
	records = data.get('data', {}).get('list', [])
	logging.debug(str(records))
	# print json.dumps(records)
	users = []
	for rec in records:
		users.append({
			'name': rec['name'],
			'user_tel': rec['user_tel'],
			'user_email': rec['user_email'],
			'user_stuffid': rec.get('user_stuffid', ''),
		})

	logging.debug(users)

	return users


def get_app_name(appId):
	uri = '/cmdb/object/instance/list/APP'
	params = {
		'appId$eq': base64.b64encode(appId.encode('utf-8'))
	}

	data = do_api_with_openapi(method='GET',
	                           uri=uri,
	                           access_key=ACCESS_KEY,
	                           secret_key=SECRET_KEY,
	                           data=params)

	records = data.get('data', {}).get('list', [])

	# print json.dumps(records)
	if len(records) > 0:
		record = records[0].get('businesses', {}).get('name', '')
	else:
		record = 'sys'

	return record


def user_info(user_list):
	sms = []
	weixin = []
	email = []
	name = []
	users = []

	if user_list:
		users = user_api(user_list)

	print users
	for user in users:
		if user['user_stuffid']:
			weixin.append(user['user_stuffid'])

		if user['user_email']:
			email.append(user['user_email'])

		if user['user_tel']:
			sms.append(user['user_tel'])

		if user['name']:
			name.append(user['name'])

	# print weixin
	sms = ','.join(list(set(sms)))  # 去重
	email = ','.join(list(set(email)))
	weixin = ','.join(list(set('DP-' + j for j in weixin if j)))
	name = ','.join(list(set(name)))
	# user_info = sms+'&'+email+'&'+weixin+'&'+name
	return sms, email, weixin, name


def main(data):
	global ACCESS_KEY
	global SECRET_KEY
	if not ACCESS_KEY or not SECRET_KEY:
		(ACCESS_KEY, SECRET_KEY) = get_the_key()

	try:
		msg = data.get('content', '')
		# name_list = data.get('receiver', [])
		name_list = [receiver["name"] for receiver in data.get('alert_receivers', [])]
		# appId = data.get('app_id', '')
		alert_dims_list = data.get('data', {}).get('alert_dims', [])
		for i in alert_dims_list:
			if i.get('name') == "_app_id":
				appId = i.get('value')
		alert_item = data.get('alert_item', 0)  # 告警项ID
		target = data.get('target', '')  # 告警对象
		org = data.get('org', 0)

		status = data.get('status', 0)
		level = 'WARNING'
		if status == 2:
			level = 'ok'

		ip = data.get('ip') or ''
		# appname = get_app_name(appId) # actually, it is a business name
		business_names = [business.get('name', '') for business in data.get('business', [])]
		business_names = list(set(business_names))
		appname = ','.join(business_names)
		sms, email, weixin, name = user_info(name_list)

		current_path = os.path.dirname(os.path.abspath(__file__))
		# param = '-n @10.253.2.178/1828#mc -a ALARM -r %s -m "%s" -b "fakid=%s;weixin_switch=on;groupid=14;appname=%s;mc_host_address=%s"' % (level, msg, weixin, appname, ip)
		if int(org) == 1888:
			weixin = 'DP-150649,DP-205151,DP-325753,DP-369443,DP-352192,DP-431701,DP-459045,DP-338706,DP-146537,DP-446355'
			sms = '13488332546,18521514738,13052318783,18801613968,15900819530,13661531347,13661748367,17091955920'
		param = '-n @10.253.2.178/3828#mc -a AOPS -r %s -m "%s" -b "aops_str=aops_event;org=%s;target=%s;alert_item=%s;mc_object_class=AOPS;fakid=%s;weixin_switch=on;sms_number=%s;sms_switch=off;groupid=14;appname=AOPS-%s;mc_host_address=%s"' % (
		level, msg, org, target, alert_item, weixin, sms, appname, ip)
		cmd = u'{current_path}/msend {param}'.format(current_path=current_path, param=param)
		# logging.debug("==" * 30)
		# logging.debug(cmd)
		s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		res = s.communicate()
		if s.returncode:
			logging.error('msend error: %s' % res[1])
		else:
			logging.info('msend success, org %s, msg %s' % (org, msg))
	# return_code, return_result = commands.getstatusoutput(cmd)
	# if return_code:
	# logging.error(u'msend error: {return_result}'.format(return_result=return_result))

	except:
		logging.error(traceback.format_exc())


if __name__ == '__main__':
	(ACCESS_KEY, SECRET_KEY) = get_the_key()
	print ACCESS_KEY
	print SECRET_KEY

	# ACCESS_KEY = '9f4f5a9a4709adacfb84c439'
	# SECRET_KEY = 'ced8bf92eeca0d34d2dda03892ea511f759c199f29f8f7f7eea35b39bc61f45f'
	# appId = '4bf57283eb5b34295e0fc06ebfb4fad3'

	data = {
		"data": {
			"content": "xxx",
			"receiver": ["lixiaobo015", "support"],
			"alert_dims": []
		}
	}
	# msg =  data.get('data', {}).get('content','')
	# name_list = data.get('data', {}).get('receiver', [])
	# appId = data.get('data', {}).get('app_id','')
	# appname = get_app_name(appId)

	msg = data.get('data', {}).get('content', '')
	name_list = data.get('data', {}).get('alert_receivers', [])
	alert_dims_list = data.get('data', {}).get('alert_dims', [])
	for i in alert_dims_list:
		if i.get('name') == "_app_id":
			appId = i.get('value')

	for i in appId:
		appname = get_app_name(i)
		print appname
		sms, email, weixin, name = user_info(name_list)
		print name_list, sms, email, weixin, name

# os.popen('/home/patrol/msend -n @192.168.68.16#mc -a ALARM  -r WARNING -m "'+msg+'" -b "fakid='+weixin+';weixin_switch=on;groupid=14;appname=定时播报"')

