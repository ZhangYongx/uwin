# _*_coding: utf-8_*_
'''
自动创建 IPMI 与 HOST 实例之间的关系。
前提条件：用户自己维护 HOST 与 IPMI 两个模型中的带外IP
'''
import requests


EASYOPS_CMDB_HOST = "10.230.20.181"
EASYOPS_ORG = 1888
EASYOPS_USER = "easyops"

HEADERS = {
	"host": "cmdb_resource.easyops-only.com",
	"org": str(EASYOPS_ORG),
	"user": EASYOPS_USER,
	"Content-Type": "application/json"
}

HEADERS_CMDB = {
	"host": "cmdb.easyops-only.com",
	"org": str(EASYOPS_ORG),
	"user": EASYOPS_USER,
	"Content-Type": "application/json"
}

# 关系 ID， 两个 OBJECT ID
RELATION_ID = "IPMISUMMARY_HOST_IPMISUMMARY_HOST"
LEFT_OBJECT_ID_IPMI = "IPMISUMMARY"
RIGHT_OBJECT_ID_HOST = "HOST"


# 两个资源模型中带外 IP 的字段 ID
IPMI_DaiWai_IP_ZiDuan_id = 'name'
HOST_DaiWai_IP_ZiDuan_id = 'adminip'  # 测试环境
# HOST_DaiWai_IP_ZiDuan_id = 'host_manageip' # 生产环境


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


def handle_relation(method, left_instance_id, right_instance_id):
	'''
	创建、更新 IPMI--HOST 的实例关系
	:param left_instance_id:
	:param right_instance_id:
	:return:  bool
	'''
	url = 'http://{0}/object_relation/{1}/relation_instance'.format(EASYOPS_CMDB_HOST, RELATION_ID)
	data = {
		"left_instance_id": left_instance_id,
		"right_instance_id": right_instance_id
	}
	r = requests.post(url=url, json=data, headers=HEADERS)

	if method == 'put':
		url = 'http://{0}/object/{1}/instance/{2}'.format(EASYOPS_CMDB_HOST, LEFT_OBJECT_ID_IPMI, left_instance_id)
		data = {
			RIGHT_OBJECT_ID_HOST: {
				"instanceId": right_instance_id
			}
		}
		r = requests.put(url=url, json=data, headers=HEADERS_CMDB)

	if r.status_code == 200 and r.json()["code"] == 0:
		return True
		# print("Creating relation between {0} and {1} \033[1;32m Success \033[0m!".format(
		# 	left_instance_id, right_instance_id))
	else:
		print("Error: {}".format(r.status_code))
		return False
		# print("Creating relation between {0} and {1} \033[1;31m Failed \033[0m!".format(
		# 	left_instance_id, right_instance_id))


if __name__ == '__main__':
	params_ipmi = {
		'fields': {
			'instanceId': 1,
			IPMI_DaiWai_IP_ZiDuan_id: 1,  # ip 字段
			RIGHT_OBJECT_ID_HOST: 1  # 对端的关系ID
		}
	}
	params_host = {
		'query': {
			HOST_DaiWai_IP_ZiDuan_id: {"$exists": True}
		},
		'fields': {
			'instanceId': 1,
			HOST_DaiWai_IP_ZiDuan_id: 1
		}
	}
	ipmi_instances_list = get_all_instance(LEFT_OBJECT_ID_IPMI, params=params_ipmi)
	host_instances_list = get_all_instance(RIGHT_OBJECT_ID_HOST, params=params_host)

	# 过虑出两个模型中共有的 IP
	# 过虑字段，生成形如 {ip: instanceId} 的字典
	ipmi_instances_dict = {}
	for i in ipmi_instances_list:
		ipmi_instances_dict[i[IPMI_DaiWai_IP_ZiDuan_id]] = i['instanceId']
	host_instances_dict = {}
	for i in host_instances_list:
		host_instances_dict[i[HOST_DaiWai_IP_ZiDuan_id]] = i['instanceId']
	# 以两个模型中的共有IP 为基准来创立关系
	common_ips = list(set(ipmi_instances_dict) & set(host_instances_dict))
	# 输出 IPMI - HOST 的差集IP
	in_ipmi_notin_host = list(set(ipmi_instances_dict) - set(host_instances_dict))
	if in_ipmi_notin_host:
		print(u"The List of IP below is in {0}, but \033[1;31m not in {1} \033[0m.".format(
			LEFT_OBJECT_ID_IPMI, RIGHT_OBJECT_ID_HOST))
		print("Those NOT handle")
		print("\n{}".format(in_ipmi_notin_host))

	print("\n----------------------------------------------")
	print("Start to create relations.........")
	for ipmi in ipmi_instances_list:
		ipmi_ip = ipmi[IPMI_DaiWai_IP_ZiDuan_id]
		ipmi_host = ipmi.get(RIGHT_OBJECT_ID_HOST)
		if ipmi_ip in common_ips:
			# IPMI['HOST'] 为空，创建关系
			if not ipmi_host:
				check_success = handle_relation('post', ipmi['instanceId'], host_instances_dict[ipmi_ip])
				if check_success:
					print("Create the relation of iLo_ip {} success.".format(ipmi_ip))
				else:
					print("Create the relation of \033[1;31m iLo_ip {} Failed \033[0m!.".format(ipmi_ip))

			# IPMI['HOST'] 已存在，检查关系是否正确。如果正确匹配，pass，否则更新关系。
			else:
				if ipmi_host[0].get(HOST_DaiWai_IP_ZiDuan_id) == ipmi_ip:
					pass
				else:
					# 必须写两次，put 第一次会先删除已有实例。第二次是创建。
					check_success = handle_relation('put', ipmi['instanceId'], host_instances_dict[ipmi_ip])
					check_success = handle_relation('put', ipmi['instanceId'], host_instances_dict[ipmi_ip])
					if check_success:
						print("Update the  relation of iLo_ip {} success.".format(ipmi_ip))
					else:
						print("Update the relation of \033[1;31m iLo_ip {} Failed \033[0m!.".format(ipmi_ip))
