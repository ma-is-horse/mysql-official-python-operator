## 创建sts的
prepare_cluster_stateful_set

## 创建deployment的
prepare_router_deployment, 最开始设置replica为0, 后续设置为实际的replica数量
有个update_size的函数来更新router deployment的数量

## 创建的时候
on_innodbcluster_create: 在InnodbCluster被创建的时候
on_pod_create: 在Pod被创建的时候
readReplicas: 这个是做什么的?

## 在哪里可以触发保证mysqlrouter的账号在MySQL里有创建
主要的函数: post_create_actions, 调用这个函数的2个地方
主要关注点在ClusterController.join_instance这里,是不是因为member_count一直没有和cr实例里的一致? 
这个member_count是通过query_membership_info用sql语句查询的, 而且并不要求集群就绪, 返回个不为reachable_member_count的成员个数就是member_count

@kopf.on.event("", "v1", "pods",
               labels={"component": "mysqld"})  # type: ignore
def on_pod_event(event, body: Body, logger: Logger, **kwargs):              
    ClusterController.on_pod_restarted
        ClusterController.reconcile_pod:
            ClusterController.join_instance:
                    if not router_objects.get_size(self.cluster) and member_count == self.cluster.parsed_spec.instances:
                        self.post_create_actions(self.dba.session, self.dba_cluster, logger)


@kopf.on.create("", "v1", "pods",
                labels={"component": "mysqld"})  # type: ignore
def on_pod_create(body: Body, logger: Logger, **kwargs):    
    ClusterController.on_pod_created:
        ClusterController.reconcile_pod:
            ClusterController.join_instance:
                    if not router_objects.get_size(self.cluster) and member_count == self.cluster.parsed_spec.instances:
                        self.post_create_actions(self.dba.session, self.dba_cluster, logger)    
                        
ClusterController.create_cluster->如果是单实例
            if self.cluster.parsed_spec.instances == 1:
                self.post_create_actions(dba.session, self.dba_cluster, logger)  

问题:
    post_create_actions里的第二个参数dba_cluster是什么? 是被创建出来的InnodbCluster里的mysqlsh拿到的cluster么?

## root用户居然是在sidecar这个容器里被创建的
- 在create_root_account函数里创建的
- 可以把mysqlrouter账号的创建也放在这里, 和上面的构成冗余
_- 只是在创建mysqlrouter账号的时候, mysql_innodb_cluster_metadata这个数据库下面的表海没有建出来, 只能grant到数据库._
- 需要更新sidecar容器的镜像


## 设置为DEBUG级别
这个只是设置mysqlsh的输出级别, operator的logger的输出日志的级别怎么设置呢?
spec:
  containers:
  - args:
    - mysqlsh
    - "--log-level=@DEBUG"
    - "--pym"
    - mysqloperator
    - operator

## operator的mysqlsh里连接实例的方式?
\c --mysql root@mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306
```txt
root in 󱃾 a223(mcamel-system) ~ via  v24.1.0 via 🐍 v3.10.4
❯ k exec -it mysql-mgr-operator-5c76547988-x8fxb  -- bash
bash-4.4$ mysqlsh
MySQL Shell 8.3.0

Copyright (c) 2016, 2023, Oracle and/or its affiliates.
Oracle is a registered trademark of Oracle Corporation and/or its affiliates.
Other names may be trademarks of their respective owners.

Type '\help' or '\?' for help; '\quit' to exit.
 MySQL  JS > \c --mysql root@mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306
Creating a Classic session to 'root@mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306'
Please provide the password for 'root@mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306': *********
Fetching schema names for auto-completion... Press ^C to stop.
Your MySQL connection id is 84984
Server version: 8.0.37 MySQL Community Server - GPL
No default schema selected; type \use <schema> to set one.
 MySQL  mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306 ssl  JS > cluster=dba.getCluster()
<Cluster:mgr1030_2>
 MySQL  mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306 ssl  JS > cluster.status()
{
    "clusterName": "mgr1030_2",
    "defaultReplicaSet": {
        "name": "default",
        "primary": "mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306",
        "ssl": "REQUIRED",
        "status": "OK",
        "statusText": "Cluster is ONLINE and can tolerate up to ONE failure.",
        "topology": {
            "mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306": {
                "address": "mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306",
                "memberRole": "PRIMARY",
                "mode": "R/W",
                "readReplicas": {},
                "replicationLag": "applier_queue_applied",
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.37"
            },
            "mgr1030-2-1.mgr1030-2-instances.default.svc.cluster.local:3306": {
                "address": "mgr1030-2-1.mgr1030-2-instances.default.svc.cluster.local:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": "applier_queue_applied",
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.37"
            },
            "mgr1030-2-2.mgr1030-2-instances.default.svc.cluster.local:3306": {
                "address": "mgr1030-2-2.mgr1030-2-instances.default.svc.cluster.local:3306",
                "memberRole": "SECONDARY",
                "mode": "R/O",
                "readReplicas": {},
                "replicationLag": "applier_queue_applied",
                "role": "HA",
                "status": "ONLINE",
                "version": "8.0.37"
            }
        },
        "topologyMode": "Single-Primary"
    },
    "groupInformationSourceMember": "mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306"
}
 MySQL  mgr1030-2-0.mgr1030-2-instances.default.svc.cluster.local:3306 ssl  JS >
```

## 查询member_count的语句
正是这条语句的查询让operator决定创建router账户并把router的deployment的replicas数量设置成期望值
```sql
SELECT m.member_id, m.member_role, m.member_state, s.view_id, m.member_version,
            (SELECT count(*) FROM performance_schema.replication_group_members) as member_count,
            (SELECT count(*) FROM performance_schema.replication_group_members WHERE member_state <> 'UNREACHABLE') as reachable_member_count
    FROM performance_schema.replication_group_members m
        JOIN performance_schema.replication_group_member_stats s
        ON m.member_id = s.member_id
    WHERE m.member_id = @@server_uuid;
```

## 重启router的deployment
```go
def restart_deployment(cluster: InnoDBCluster, logger: Logger)->None:
    def inner_restart(ns:str, name: str, replicas: int)->None:
        api_apps.patch_namespaced_deployment(name, ns, body={"spec": {"replicas": replicas}})
    deploy = cluster.get_router_deployment()
    if not deploy:
        return None
    size = deploy.spec.replicas
    meta = deploy.metadata
    namespace_name = f"{meta.namespace}/{meta.name}"
    if size:
        logger.info(f"Restarting the router's deployment for cluster {namespace_name}, replicas = {size}")
        inner_restart(meta.namespace, meta.name, 0)
        inner_restart(meta.namespace, meta.name, size)
        return None
    else:
        logger.info(f"Conditions not met, giving up on restarting the cluster {namespace_name}")
        return None
```