<template>
<div>
  <b-table bordered :busy=table_busy :items="triggers_info" :fields="fields" label-sort-asc="" label-sort-desc="" sort-desc sort-by="name" :tbody-tr-class="rowClass" >
    <template #table-busy>
      <div class="text-center text-info my-2">
        <b-spinner class="align-middle"></b-spinner>
        <strong>Loading...</strong>
      </div>
    </template>
    <template #cell(actions)="row">
      <b-dropdown id="dropdown-1" text="Actions" class="m-md-1" variant="primary" right>
        <b-dropdown-item @click="toggle_enable(row)">Toggle Enable</b-dropdown-item>
        <b-dropdown-item @click="show_jobs(row)">Show Jobs</b-dropdown-item>
        <b-dropdown-item @click="show_input(row)">Show Input</b-dropdown-item>
      </b-dropdown>
    </template>
  </b-table>

  <SimpleModal ref="simple_modal" />
</div>
</template>

<script>
import axios from 'axios';
import utils from '/src/utils.js';
import SimpleModal from '@/components/SimpleModal.vue'

export default {
  name: 'JobTable',
  components: {
    SimpleModal,
  },
  data() {
    return {
      table_busy: false,
      triggers_info: [],
      fields: [
        {key: 'name', label: 'Name', tdClass: 'align-middle', sortable: true},
        {key: 'trigger_class', label: 'Trigger Class', tdClass: 'align-middle', sortable: true},
        {key: 'owner', label: 'Owner', tdClass: 'align-middle', sortable: true},
        {key: 'update_timestamp', label: 'Update Time', tdClass: 'align-middle', sortable: true},
        {key: 'notification_channel', label: 'Notification Channel', tdClass: 'align-middle', sortable: true},
        {key: 'enabled', label: 'Enabled', tdClass: 'align-middle', sortable: true},
        {key: 'actions', label: 'Actions', tdClass: 'align-middle', sortable: true},
      ],
    }
  },
  created() {
    const frontend_endpoint = utils.getFrontendEndpoint();

    this.show_pagination = false;
    this.table_busy = true;

    axios.post(
      `${frontend_endpoint}/list_triggers`,
    ).then(response => {
      console.log(response);

      let triggers_info = []

      for (let i = 0; i < response.data.length; i++)
      {
        triggers_info.push({
          name: response.data[i]["_id"],
          trigger_class: response.data[i]["trigger_class"],
          owner: response.data[i]["owner"],
          update_timestamp: utils.getTimeString(response.data[i]["update_timestamp"]),
          notification_channel: response.data[i]["notification_channel"],
          enabled: response.data[i]["enabled"],
          input_json: response.data[i]["input_json"],
        })
      }

      this.triggers_info = triggers_info;
      this.job_number = triggers_info.length;

      this.show_pagination = true;
      this.table_busy = false;
    }).catch(e => {
      console.log(e);
    })
  },
  methods: {
    rowClass: function(item) {
      if (item == null)
        return

      if (item.enabled)
        return 'table-success';
      else
        return 'table-secondary';
    },
    toggle_enable: function(item) {
      const frontend_endpoint = utils.getFrontendEndpoint();

      let query_path = item.item.enabled ? "/disable_trigger" : "/enable_trigger";
      let target_state = !item.item.enabled;

      axios.post(
        `${frontend_endpoint}${query_path}`,
        {
          trigger_name: item.item.name,
        }
      ).then(() => {
        item.item.enabled = target_state;

        this.$refs.simple_modal.show(
          "Toggle Trigger Enable",
          target_state ? `Trigger ${item.item.name} enabled.` :`Trigger ${item.item.name} disabled.`,
        )
      }).catch(e => {
        this.$refs.simple_modal.show(
          "Error",
          `Failed to toggle trigger ${item.item.name} enable: ${e}`,
        );
      })
    },
    show_jobs: function(item) {
      let params = new URLSearchParams();
      params.set("tag_filter", item.item.name);

      window.location.href = `/jobs?${params.toString()}`;
    },
    show_input: function(item) {
      this.$refs.simple_modal.show(
        "Trigger Input",
        "<pre>" + JSON.stringify(JSON.parse(item.item.input_json), null, 2) + "</pre>",
      );
    },
  },
}
</script>

<style scoped>
</style>
