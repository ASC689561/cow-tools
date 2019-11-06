import consul
import streamlit as st
from consul import Check

st.header("Consul Tools")

consul_endpoint = st.sidebar.text_input("Consul Endpoint", 'localhost:8500')
host, port = consul_endpoint.split(':')
port = int(port)

c = consul.Consul(host=host, port=port)


class UI:

    def run(self): pass


class Register(UI):
    name = 'Register Service'

    def __init__(self):
        svc = c.agent.services()
        selected_service = st.selectbox("Existing service", list(svc))

        if selected_service:
            self.txt_name = st.text_input("Service ID", svc[selected_service]['ID'])
            self.txt_url = st.text_input("Service URL", svc[selected_service]['Address'])
            checks = c.health.checks(selected_service)
        else:
            self.txt_name = st.text_input("Service Name", "test-service")
            self.txt_url = st.text_input("Service URL", 'http://www.google.com')

        self.num_interval = st.number_input("Interval(s)", 5, 300, 30)
        self.num_timeout = st.number_input("Timeout(s)", 5, 120, 60)
        self.register_btn = st.button("Register")

    def run(self):
        if self.register_btn:
            check = Check.http(self.txt_url, interval=f'{self.num_interval}s', timeout=f'{self.num_timeout}s')
            c.agent.service.register(name=self.txt_name,
                                     service_id=self.txt_name,
                                     address=self.txt_url, check=check)


class ListService(UI):
    name = 'List Services'

    def __init__(self):
        st.subheader("Services")
        st.write(c.agent.services())

        st.subheader("Checks")
        st.write(c.agent.checks())

    def run(self):
        pass


class AlertConfig(UI):
    name = 'Alerts'

    def get_value(self, key, default):
        index, value = c.kv.get(key)
        if not value:
            return default
        return value['Value'].decode()

    def __init__(self):
        self.change_threshold = st.number_input("Change Threshold", 10, 120, 20)
        self.enabled = st.checkbox("Slack Enabled", self.get_value('consul-alerts/config/notifiers/slack/enabled', 'True'))
        self.slack_detailed = st.checkbox("Slack Detailed", self.get_value('consul-alerts/config/notifiers/slack/detailed', 'True'))

        self.slack_username = st.text_input("Slack Username", self.get_value('consul-alerts/config/notifiers/slack/username', 'Consul'))
        self.slack_channel = st.text_input("Slack Channel", self.get_value('consul-alerts/config/notifiers/slack/channel', '<channel>'))
        self.slack_url = st.text_input("Slack URL", self.get_value('consul-alerts/config/notifiers/slack/url', '<Slack webhook url>'))
        self.btn_register = st.button("Register")

    def run(self):
        if self.btn_register:
            c.kv.put('consul-alerts/config/checks/change-threshold', str(self.change_threshold))
            c.kv.put('consul-alerts/config/notifiers/slack/enabled', str(self.enabled))
            c.kv.put('consul-alerts/config/notifiers/slack/username', str(self.slack_username))
            c.kv.put('consul-alerts/config/notifiers/slack/channel', str(self.slack_channel))
            c.kv.put('consul-alerts/config/notifiers/slack/detailed', str(self.slack_detailed))
            c.kv.put('consul-alerts/config/notifiers/slack/url', str(self.slack_url))


class DeleteService(UI):
    name = 'Delete Services'

    def __init__(self):
        all_svc = list(c.agent.services())
        self.service = st.multiselect("Services", all_svc)
        self.delete_btn = st.button("Delete")

    def run(self):
        if self.delete_btn:
            for v in self.service:
                st.write(v)
                c.agent.service.deregister(v)


def get_subclasses(cls):
    """returns all subclasses of argument, cls"""
    if issubclass(cls, type):
        subclasses = cls.__subclasses__(cls)
    else:
        subclasses = cls.__subclasses__()
    for subclass in subclasses:
        subclasses.extend(get_subclasses(subclass))
    return subclasses


all_class = {x.name: x for x in get_subclasses(UI)}
arr = list(all_class.keys())
task = st.sidebar.selectbox('Function', arr)

t = all_class[task]
e = t()
e.run()
