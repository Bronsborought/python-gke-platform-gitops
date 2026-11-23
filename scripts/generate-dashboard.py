import json
from pathlib import Path

scope = 'namespace=~"$namespace",service="python-platform"'
req = 'http_requests_total{' + scope + ',path!~"/healthz|/ready"}'
err = 'http_requests_total{' + scope + ',status_code=~"5..",path!~"/healthz|/ready"}'
lat = 'http_request_duration_seconds_bucket{' + scope + ',path!~"/healthz|/ready"}'
cpu = 'namespace=~"$namespace",pod=~"python-platform-.*",container="app"'
queries = [
 ('Request rate', 'reqps', [('RPS', f'sum(rate({req}[2m]))')]),
 ('5xx responses', 'percent', [('5xx %', f'100 * ((sum(rate({err}[2m])) or vector(0)) / clamp_min(sum(rate({req}[2m])), 0.001))')]),
 ('Latency', 's', [(f'p{int(q*100)}', f'histogram_quantile({q}, sum by (le) (rate({lat}[2m])))') for q in (.5, .95, .99)]),
 ('CPU usage per pod', 'cores', [('{{pod}}', f'sum by (pod) (rate(container_cpu_usage_seconds_total{{{cpu}}}[2m]))')]),
 ('Memory working set', 'bytes', [('{{pod}}', f'max by (pod) (container_memory_working_set_bytes{{{cpu}}})')]),
 ('CPU throttled periods', 'percent', [('{{pod}}', f'100 * sum by (pod) (rate(container_cpu_cfs_throttled_periods_total{{{cpu}}}[2m])) / clamp_min(sum by (pod) (rate(container_cpu_cfs_periods_total{{{cpu}}}[2m])), 0.001)')]),
 ('PVC used', 'percent', [('{{namespace}}', '100 * max by (namespace) (kubelet_volume_stats_used_bytes{namespace=~"$namespace",persistentvolumeclaim="python-platform-data"} / kubelet_volume_stats_capacity_bytes{namespace=~"$namespace",persistentvolumeclaim="python-platform-data"})')]),
 ('Memory limit usage', 'percent', [('{{pod}}', f'100 * max by (namespace,pod,container) (container_memory_working_set_bytes{{{cpu}}}) / on(namespace,pod,container) max by (namespace,pod,container) (kube_pod_container_resource_limits{{namespace=~"$namespace",pod=~"python-platform-.*",container="app",resource="memory",unit="byte"}})')]),
]
panels = []
for i, (title, unit, targets) in enumerate(queries):
    panels.append({'id':i+1,'type':'timeseries','title':title,
      'datasource':{'type':'prometheus','uid':'${DS_PROMETHEUS}'},
      'gridPos':{'x':(i%2)*12,'y':(i//2)*8,'w':12,'h':8},
      'fieldConfig':{'defaults':{'unit':unit},'overrides':[]},
      'targets':[{'refId':chr(65+j),'expr':expr,'legendFormat':legend} for j,(legend,expr) in enumerate(targets)]})
dashboard = {'uid':'python-platform','title':'Python GKE Platform','schemaVersion':39,
 'version':1,'editable':True,'timezone':'browser','refresh':'15s','tags':['python-platform'],
 'time':{'from':'now-30m','to':'now'},'panels':panels,
 'templating':{'list':[
  {'name':'DS_PROMETHEUS','type':'datasource','query':'prometheus','label':'Prometheus'},
  {'name':'namespace','type':'custom','query':'platform-staging,platform-production',
   'current':{'text':'platform-staging','value':'platform-staging'},'multi':False,'includeAll':False}]}}
p = Path('monitoring/resources/dashboard.yaml')
body = json.dumps(dashboard, indent=2)
p.write_text('apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: python-platform-dashboard\n  namespace: monitoring\n  labels:\n    grafana_dashboard: "1"\ndata:\n  python-platform.json: |\n' + '\n'.join('    '+line for line in body.splitlines()) + '\n')
