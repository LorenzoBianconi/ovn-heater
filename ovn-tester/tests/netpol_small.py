from collections import namedtuple
from ovn_context import Context
from ovn_workload import Namespace

NpSmallCfg = namedtuple('NpSmallCfg',
                        ['n_ns',
                         'labels_ns_ratio',
                         'pods_ns_ratio'])

class NetpolSmall(object):
    def __init__(self, config):
        self.config = NpSmallCfg(
            n_ns=config.get('n_ns', 0),
            labels_ns_ratio=config.get('labels_ns_ratio', 0),
            pods_ns_ratio=config.get('pods_ns_ratio', 0),
        )

    def run(self, ovn, global_cfg):
        all_labels = []
        all_ns = []
    
        with Context('netpol_small_startup', brief_report=True) as ctx:
            ports = ovn.provision_ports(
                    self.config.pods_ns_ratio*self.config.n_ns)
            for i in range(self.config.n_ns):
                ns = Namespace(ovn, f'NS_{i}')
                ns.add_ports(ports[i*self.config.pods_ns_ratio :
                                   (i + 1)*self.config.pods_ns_ratio])
                all_ns.append(ns)
                for l in range(self.config.labels_ns_ratio):
                    for p in range(self.config.pods_ns_ratio):
                        if p % self.config.labels_ns_ratio == l:
                            all_labels.append(ns.ports[p])
    
        with Context('netpol_small', self.config.n_ns) as ctx:
            for i in ctx:
                ns_labels = all_labels[i*self.config.pods_ns_ratio :
                                       (i + 1)*self.config.pods_ns_ratio]
                for l in range(self.config.labels_ns_ratio):
                    label = ns_labels[l*self.config.labels_ns_ratio :
                                      (l+1)*self.config.labels_ns_ratio]
                    addr_set = ovn.nbctl.address_set_create(f'as_ns_{l}')
                    ovn.nbctl.address_set_add_addrs(addr_set,
                                                    [str(p.ip) for p in label])
                    pg = ovn.nbctl.port_group_create(f'pg_ns_{l}')
                    ovn.nbctl.port_group_add_ports(pg, label)
    
        if not global_cfg.cleanup:
            return
        with Context('netpol_small_cleanup', brief_report=True) as ctx:
            for ns in all_ns:
                ns.unprovision()
    
