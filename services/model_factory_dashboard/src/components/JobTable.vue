<template>
<div v-show=show_component>
  <b-table id="job-table" perPage="20" :current-page="current_page" bordered :busy=table_busy :items="jobs_info" :fields="fields" label-sort-asc="" label-sort-desc="" :tbody-tr-class="rowClass" sort-desc sort-by="creation_timestamp" >
    <template #table-busy>
      <div class="text-center text-info my-2">
        <b-spinner class="align-middle"></b-spinner>
        <strong>Loading...</strong>
      </div>
    </template>
    <template #cell(actions)="row">
      <b-dropdown id="dropdown-1" text="Actions" class="m-md-1" variant="primary" right>
        <b-dropdown-item @click="show_job_info(row)">Show Info</b-dropdown-item>
        <b-dropdown-item @click="hide_job(row)">Hide</b-dropdown-item>
        <b-dropdown-item @click="show_job_log(row)">Show Log</b-dropdown-item>
      </b-dropdown>
    </template>
  </b-table>

  <b-pagination class="pagination" v-show="show_pagination" v-model="current_page" :total-rows="job_number" :per-page="20" aria-controls="jobs-table" align="center" first-number last-number pills />

  <SimpleModal ref="simple_modal" />
</div>
</template>

<script>
import axios from 'axios';
import utils from '/src/utils.js';
import SimpleModal from '@/components/SimpleModal.vue'

export default {
  name: 'JobTable',
  data() {
    return {
      show_pagination: false,
      job_number: 0,
      current_page: 1,
      show_component: false,
      table_busy: false,
      jobs_info: [],
      fields: [
        {key: 'job_id', label: 'Job ID', tdClass: 'align-middle', sortable: true},
        {key: 'pipeline', label: 'Pipeline', tdClass: 'align-middle', sortable: true},
        {key: 'operator_id', label: 'Operator ID', tdClass: 'align-middle', sortable: true},
        {key: 'tags', label: 'Tags', tdClass: 'align-middle', sortable: true},
        {key: 'pool', label: 'Pool', tdClass: 'align-middle', sortable: true},
        {key: 'creation_timestamp', label: 'Creation Timestamp', tdClass: 'align-middle', sortable: true},
        {key: 'start_timestamp', label: 'Start Timestamp', tdClass: 'align-middle', sortable: true},
        {key: 'completion_timestamp', label: 'Completion Timestamp', tdClass: 'align-middle', sortable: true},
        {key: 'owner', label: 'Owner', tdClass: 'align-middle', sortable: true},
        {key: 'stage', label: 'Stage', tdClass: 'align-middle', sortable: true},
        {key: 'status', label: 'Status', tdClass: 'align-middle', sortable: true},
        {key: 'actions', label: 'Actions', tdClass: 'align-middle', sortable: true},
      ],
      action_title: undefined,
      action_content: undefined,
    }
  },
  components: {
    SimpleModal,
  },
  methods: {
    show_job_info: function(row) {
      const frontend_endpoint = utils.getFrontendEndpoint();

      axios.post(
        `${frontend_endpoint}/get_info_for_single_job`,
        {
          job_id: row.item.job_id,
        }
      ).then(response => {
        console.log(response);

        let title = "Job Info";
        let text = "<pre>" + JSON.stringify({
          "job_id": response.data.job_id,
          "parent_job_id": response.data.parent_job_id,
          "pipeline_name": response.data.pipeline_name,
          "pipeline_params": response.data.pipeline_params,
          "operator_id": response.data.operator_id,
          "pool": response.data.pool,
          "docker_image_repo": response.data.docker_image_repo,
          "docker_image_tag": response.data.docker_image_tag,
          "docker_image_digest": response.data.docker_image_digest,
          "execution_mode": response.data.execution_mode,
          "cmd": response.data.cmd,
          "owner": response.data.owner,
          "creator_host": response.data.creator_host,
          "tags": response.data.tags,
          "cpu_request": response.data.cpu_request,
          "memory_request": response.data.memory_request,
          "storage_request": response.data.storage_request,
          "gpu_request": response.data.gpu_request,
          "ttl_after_finished": response.data.ttl_after_finished,
          "notification_channel": response.data.notification_channel,
        }, null, 2) + "</pre>";

        this.$refs.simple_modal.show(title, text, "xl");
      }).catch(e => {
        console.log(e);
      });
    },
    hide_job: function(row) {
      const frontend_endpoint = utils.getFrontendEndpoint();

      axios.post(
        `${frontend_endpoint}/tag_job`,
        {
          job_id: row.item.job_id,
          tag: "hide",
        }
      ).then(() => {
        this.$refs.simple_modal.show(
          "Hide Job",
          `Hide job ${row.item.job_id}. Please refresh the page to reflect the change.`,
        );
      }).catch(e => {
        console.log(e);
      });
    },
    show_job_log: function(row) {
      const frontend_endpoint = utils.getFrontendEndpoint();

      console.log("retrieving k8s job", row);
      axios.post(
        `${frontend_endpoint}/get_k8s_job_log`,
        {
          job_id: row.item.job_id,
          pod_name: row.item.pod_name,
        }
      ).then(response => {
        console.log(response);

        this.$refs.simple_modal.show(
          "Job Log",
          response.data.length ? `<pre>${response.data}</pre>` : "Failed to get job log",
          "xl",
        );
      }).catch(e => {
        console.log(e);

        this.$refs.simple_modal.show(
          "Error",
          "Failed to get job log: \n" + e,
        )
      });
    },
    rowClass: function(item) {
      if (item == null)
        return

      if (item.status == "succeeded")
        return 'table-success';
      else if (item.status == "failed")
        return 'table-danger';
      else if (item.status == "deleted")
        return 'table-secondary';
      else if (item.status == "pending")
        return 'table-warning';
      else if (item.status == "running")
        return 'table-info';
    },
    load: function(
      job_id_filter,
      pipeline_filter,
      operator_id_filter,
      pool_filter,
      tag_filter,
      owner_filter,
      status_filter,
    ) {
      axios.defaults.headers.post['Content-Type'] ='application/x-www-form-urlencoded';

      this.show_component = true;

      const frontend_endpoint = utils.getFrontendEndpoint();

      let job_filter = {
        tags: {"$nin": ["hide"]},
      }

      if (job_id_filter)
        job_filter["job_id"] = job_id_filter;

      if (pipeline_filter)
        job_filter["pipeline_name"] = pipeline_filter;

      if (operator_id_filter)
        job_filter["operator_id"] = operator_id_filter;

      if (pool_filter)
        job_filter["pool"] = pool_filter;

      if (tag_filter)
        job_filter["tags"]["$in"] = [tag_filter];

      if (owner_filter)
        job_filter["owner"] = owner_filter;

      if (status_filter)
        job_filter["status"] = status_filter;

      this.show_pagination = false;
      this.table_busy = true;

      axios.post(
        `${frontend_endpoint}/get_info_for_jobs`,
        {
          job_filter: JSON.stringify(job_filter),
          job_fields: '["job_id", "parent_job_id", "pipeline_name", "pipeline_params", "operator_id", "pool", "owner", "docker_image_repo", "docker_image_tag", "docker_image_digest", "execution_mode", "tags", "creator_host", "cmd", "pod_name", "ip_addr", "stage", "output", "ttl_after_finished", "resources.cpu_request", "resources.memory_request", "resources.storage_request", "resources.gpu_request", "creation_timestamp", "start_timestamp", "completion_timestamp", "notification_channel", "pending_notification_sent", "completion_notification_sent", "status", "exit_code", "exit_reason", "exception", "archived", "exception"]',
        }
      ).then(response => {
        let jobs_info = []

        for (let i = 0; i < response.data.length; i++)
        {
          jobs_info.push({
            job_id: response.data[i]["_id"],
            pipeline: response.data[i]["pipeline_name"],
            operator_id: response.data[i]["operator_id"],
            pool: response.data[i]["pool"],
            tags: response.data[i]["tags"] && response.data[i]["tags"].join(", "),
            creation_timestamp: utils.getTimeString(response.data[i]["creation_timestamp"]),
            start_timestamp: utils.getTimeString(response.data[i]["start_timestamp"]),
            completion_timestamp: utils.getTimeString(response.data[i]["completion_timestamp"]),
            owner: response.data[i]["owner"],
            stage: response.data[i]["stage"],
            status: response.data[i]["status"],
          })
        }

        this.jobs_info = jobs_info;
        this.job_number = jobs_info.length;

        this.show_pagination = true;
        this.table_busy = false;
      }).catch(e => {
        console.log(e);
      })
    }
  },
}
</script>

<style scoped>
</style>
