## 打包
~~如何打包生成镜像?
- bash gen_dockerfile.sh, 生成Dockerfile
- 这个Dockerfile的基础镜像又需要build_deps.sh来生成?~~

所以,这种打包不可取, 有些东西没有发布出来,比如`build_deps.sh`的一些参数, 只能采用[CONTRIBUTING.md](CONTRIBUTING.md)里的`Building a test image`的方式  
```Dockerfile
ARG BASE_VERSION=9.4.0-2.2.5
FROM container-registry.oracle.com/mysql/community-operator:$BASE_VERSION
# 文档里给的指令是错的, 第二个参数少了mysqloperator/
COPY mysqloperator/ /usr/lib/mysqlsh/python-packages/mysqloperator/
```

## operator和mysql-server版本的匹配 
community-operator:9.4.0-2.2.5和community-server:8.4.5,启动的pod里的sidecar容器报:
```txt
[2025-09-10 08:55:52,899] sidecar              [INFO    ] MySQL Operator/sidecar_main.py=2.2.5 timestamp=2025-07-17T19:27:51 kopf=1.37.4 uid=27
[2025-09-10 08:55:52,931] sidecar              [INFO    ] My pod is mabing0910-2 in default
[2025-09-10 08:55:52,931] sidecar              [INFO    ] Bootstrapping
[2025-09-10 08:55:52,939] sidecar              [INFO    ] Connect attempt #0 successful
[2025-09-10 08:55:52,940] sidecar              [INFO    ] Metadata check failed: MySQL Error (1049): Unknown database 'mysql_innodb_cluster_metadata'
[2025-09-10 08:55:52,941] sidecar              [INFO    ] Configuring mysql pod default/mabing0910-2, configured=None datadir=['/var/lib/mysql']
[2025-09-10 08:55:52,941] sidecar              [INFO    ] Creating root account
[2025-09-10 08:55:52,948] sidecar              [INFO    ] DROP USER root@localhost - Warnings [["Note", 3162, "Authorization ID 'root'@'localhost' does not exist."]]
[2025-09-10 08:55:52,948] sidecar              [INFO    ] Creating own root account replace me with a username like root@%
Traceback (most recent call last):
  File "/usr/lib/mysqlsh/python-packages/mysqloperator/sidecar_main.py", line 635, in bootstrap
    initialize(session, datadir, pod, cluster, logger)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/mysqlsh/python-packages/mysqloperator/sidecar_main.py", line 515, in initialize
    create_root_account(session, pod, cluster, logger)
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/mysqlsh/python-packages/mysqloperator/sidecar_main.py", line 429, in create_root_account
    ret = session.run_sql("CREATE USER IF NOT EXISTS ?@? IDENTIFIED BY ?", [user, host, password])
mysqlsh.DBError: MySQL Error (1470): String 'replace me with a username like root' is too long for user name (should be no longer than 32)
[2025-09-10 08:55:52,951] sidecar              [CRITICAL] Unhandled exception while bootstrapping MySQL: MySQL Error (1470): String 'replace me with a username like root' is too long for user name (should be no longer than 32)
[2025-09-10 08:55:52,951] sidecar              [INFO    ] Bootstrap error -1
```
应该是创建ic的时候[my_example.yaml](samples/my_example.yaml)的secret的`rootUser`字段值需要修改, 把'replace me with a username like root'改为用户名,比如root,`rootPassword`的值也要修改

## 登录
mysql -h 10.6.178.178 -P 30529 -uroot -p'root@123!'

## router
### 下载安装
- https://dev.mysql.com/downloads/router/, 这里只能下到LTS之类的版本
- https://downloads.mysql.com/archives/router/, 这里能下到所有版本
- 对应的rnc版本: https://github.com/containerd/containerd/blob/v1.7.16/script/setup/runc-version
### docker
官方: https://dev.mysql.com/doc/mysql-router/8.0/en/mysql-router-installation-docker.html
```bash
docker run \
  -e MYSQL_HOST=localhost \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=mysql \
  -e MYSQL_PASSWORD=mysql \
  -e MYSQL_INNODB_CLUSTER_MEMBERS=3 \
  -e MYSQL_ROUTER_BOOTSTRAP_EXTRA_OPTIONS="--conf-use-sockets --conf-use-gr-notifications" \
  -ti container-registry.oracle.com/mysql/community-router
```
自己配合[svc.yaml](samples/router/svc.yaml)修改的,把在K8S里的InnodbCluster的副本数改为1, 和下面的MYSQL_INNODB_CLUSTER_MEMBERS一致  
这里的6446端口是从/tmp/mysqlrouter.conf里来的  
```bash
nerdctl run \
  -e MYSQL_HOST=10.6.178.178 \
  -e MYSQL_PORT=31232 \
  -e MYSQL_USER=root \
  -e MYSQL_CREATE_ROUTER_USER=0 \
  -e MYSQL_PASSWORD=root@123! \
  -e MYSQL_INNODB_CLUSTER_MEMBERS=1 \
  -e MYSQL_ROUTER_BOOTSTRAP_EXTRA_OPTIONS="--conf-use-sockets --conf-use-gr-notifications" \
  -p 6446:6446 \
  -d release-ci.daocloud.io/demo/community-router:8.4.5
```
在容器里面访问:
```bash
mysql -uroot -proot@123! -P31232
```
在容器外部访问
```bash
mysql -uroot -proot@123! -P6446 -h10.6.178.200
```
如果mgr是跑在k8s集群里的话, router不在k8s集群里,会有如下错误,应该是因为mgr启动的各个节点的地址就是这么配置的,无解
```txt
2025-09-10 17:40:27 metadata_cache WARNING [7f37087d0640] Failed connecting with Metadata Server mabing0910-0.mabing0910-instances.default.svc.cluster.local:3306: Unknown MySQL server host 'mabing0910-0.mabing0910-instances.default.svc.cluster.local' (-2) (2005)
2025-09-10 17:40:27 metadata_cache ERROR [7f37087d0640] Failed fetching metadata from any of the 1 metadata servers.

2025-09-10 17:40:52 routing WARNING [7f37017fa640] No available servers found for PRIMARY routing
2025-09-10 17:40:53 routing WARNING [7f37017fa640] No available servers found for PRIMARY routing
2025-09-10 17:40:55 routing WARNING [7f37017fa640] No available servers found for PRIMARY routing
2025-09-10 17:40:55 routing ERROR [7f37037fe640] [routing:bootstrap_rw] connecting to backend(s) for client from 10.64.40.111:7746 failed: no destinations: no more destinations
2025-09-10 17:40:55 routing INFO [7f37037fe640] Stop accepting connections for routing routing:bootstrap_rw listening on 0.0.0.0:6446
2025-09-10 17:40:55 routing INFO [7f37037fe640] Stop accepting connections for routing routing:bootstrap_rw listening on /tmp/mysqlrouter/mysql.sock
```
上面的错误需要把mgr跑在传统的linux服务器上

## router修改某个配置
### 用配置文件覆盖
就是`samples/router`目录里的deploy资源和cm资源配合
- [router-deploy-with-extra-config.yaml](samples/router/router-deploy-with-extra-config.yaml)
- [router-extra-config.yaml](samples/router/router-extra-config.yaml)
### 命令行
https://dev.mysql.com/doc/mysql-router/8.0/en/mysql-router-command-options-runtime.html
- `--bootstrap`后面跟的是server_url,写法:
- 上面链接里的第二种方式就是`用配置文件覆盖`的方式

## router的用户没有创建出来
在8.3.0-2.1.2版本的operaotr创建实例的过程中偶尔出现mysqlrouter这个账号在mysql里没有被创建出来, 这个账号对应的k8s的secret是有的
```sql
mysql> select user,host from mysql.user; -- 正常的是应该有mysqlrouter这个账号的
+---------------------------+-----------+
| user                      | host      |
+---------------------------+-----------+
| mysql_innodb_cluster_1000 | %         |
| mysqladmin                | %         |
| mysqlbackup               | %         |
| mysqlrouter               | %         |
| root                      | %         |
| localroot                 | localhost |
| mysql.infoschema          | localhost |
| mysql.session             | localhost |
| mysql.sys                 | localhost |
| mysqlhealthchecker        | localhost |
| mysqlmetrics              | localhost |
+---------------------------+-----------+
11 rows in set (0.00 sec)
```

### 在集群启动的时候,创建mysqlrouter账号
```python
def post_create_actions(self, session: 'ClassicSession', dba_cluster: 'Cluster', logger: Logger)
```

在最新版的代码里,有下面的语句可能解决这个问题?
```python
# commit: 9ea5ee8758db4e9be69a0eb88da722a8732f5329
operator_cluster.ensure_router_accounts_are_uptodate(clusters, logger)
```
### 验证
在mysql里把`mysqlrouter`这个账号的信息删除掉, 重启(或者不重启)operator, 看operator能否根据secret自动在mysql里创建这个账号.  
只是去update,如果账号信息不存在,无法创建就会报错, operator相关的日志如下:  
```txt
Traceback (most recent call last):
  File "/usr/lib/mysqlsh/python-packages/kopf/_core/actions/execution.py", line 276, in execute_handler_once
    result = await invoke_handler(
             ^^^^^^^^^^^^^^^^^^^^^
    ...<9 lines>...
    )
    ^
  File "/usr/lib/mysqlsh/python-packages/kopf/_core/actions/execution.py", line 371, in invoke_handler
    result = await invocation.invoke(
             ^^^^^^^^^^^^^^^^^^^^^^^^
    ...<9 lines>...
    )
    ^
  File "/usr/lib/mysqlsh/python-packages/kopf/_core/actions/invocation.py", line 139, in invoke
    await asyncio.shield(future)  # slightly expensive: creates tasks
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/mysqlsh/lib/python3.13/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/usr/lib/mysqlsh/python-packages/mysqloperator/controller/operator.py", line 46, in on_startup
    operator_cluster.ensure_router_accounts_are_uptodate(clusters, logger)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/usr/lib/mysqlsh/python-packages/mysqloperator/controller/innodbcluster/operator_cluster.py", line 64, in ensure_router_accounts_are_uptodate
    router_objects.update_router_account(cluster,
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^
                                         lambda: logger.warning(f"Cluster {cluster.namespace}/{cluster.name} unreachable"),
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                         logger)
                                         ^^^^^^^
  File "/usr/lib/mysqlsh/python-packages/mysqloperator/controller/innodbcluster/router_objects.py", line 489, in update_router_account
    dba.get_cluster().setup_router_account(user, {"update": True})
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
RuntimeError: Could not proceed with the operation because account mysqlrouter-F7dZRnLydN@% does not exist and the 'update' option is enabled
```