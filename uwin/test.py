# _*_coding: utf-8_*_

import json
import requests


EASYOPS_CMDB_HOST = "10.230.20.181"
EASYOPS_ORG = 1888
EASYOPS_USER = "easyops"


HEADERS ={
	"host": "cmdb.easyops-only.com",
	"org": str(EASYOPS_ORG),
	"user": EASYOPS_USER,
	"Content-Type": "application/json"
}

RELATION_ID = "IPMISUMMARY_HOST_IPMISUMMARY_HOST"
LEFT_OBJECT_ID_IPMI = "IPMISUMMARY"
RIGHT_OBJECT_ID_HOST = "HOST"


def cmdb_request(method, url, params=None):
	try:
		r = requests.request(method=method, url=url, headers=HEADERS, json=params)
		if r.status_code == 200:
			r_json = r.json()
			if r_json["code"] == 0:
				return r_json
			else:
				print(u'the response code error:{0}'.format(r_json["code"]))
				return None
		else:
			print(u'the response status code:{0}'.format(r.status_code))
			return None
	except Exception as e:
		print(e)
		return None


# def get_object_id():
# 	'''
# 	获取两个资源模型的 object_id
# 	'''
# 	url = "http://{0}/object_relation/{1}".format(EASYOPS_CMDB_HOST, RELATION_ID)
# 	r_data = cmdb_request("GET", url)["data"]
# 	left_object_id, right_object_id= r_data["left_object_id"], r_data["right_object_id"]
# 	return left_object_id, right_object_id


def get_all_instance(object_id, params=None, pagesize=3000):
	'''
	获取所有实例
	:param object_id: 模型 id
	:param params: 页面
	:param pagesize: 页面容量
	:return: list = [instance_id,name]
	'''
	url = "http://{0}/object/{1}/instance/_search".format(EASYOPS_CMDB_HOST, object_id)
	if params is None:
		params = {}
	params['page'] = 1
	params['page_size'] = pagesize
	# 过虑出 name 和 instance_id
	params['fields'] = {
		'instanceId': 1,
		'name': 1,
		'ip': 1,
		'HOST': 0
	}

	try:
		r_json = cmdb_request("POST", url, params)
		if r_json:
			if int(r_json['data']['total']) > pagesize:
				pages = int(r_json['data']['total']) // pagesize
				res = r_json['data']['list']
				for _ in range(2, pages + 2):
					params['page'] = _
					res = res + cmdb_request('POST', url, pagesize)['data']['list']
					return res
			else:
				return r_json['data']['list']
		else:
			return []

	except Exception as e:
		print("get_all_instance error: " + e)


def create_relation(left_instance_id, right_instance_id):
	url = "http://{0}/object_relation/{1}/relation_instance".format(EASYOPS_CMDB_HOST, RELATION_ID)
	data = {
		"left_instance_id": left_instance_id,
		"right_instance_id": right_instance_id
	}
	r = requests.post(url=url, data=data, headers=HEADERS)
	if r.status_code ==200:
		r_json = r.json()
		if r_json["code"] == 0:
			print("Relating the {0} and {1} \033[1;32m Success \033!".format(left_instance_id, right_instance_id))
		if r_json["code"] == 13360:
			pass
		else:
			print("Relating the {0} and {1} \033[1;31m Failed \033!".format(left_instance_id, right_instance_id))
	else:
		print("Error: {}".format(r.status_code))


if __name__ == '__main__':
	ipmi_instances_list = get_all_instance(LEFT_OBJECT_ID_IPMI)
	host_instances_list = get_all_instance(RIGHT_OBJECT_ID_HOST)
