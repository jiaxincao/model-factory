export default {
  getCurrentParam: function(key) {
    const urlParams = new URLSearchParams(location.search);
    return urlParams.get(key);
  },
  getFrontendEndpoint: function() {
    return "http://192.168.1.102:5000";
  },
  getTimeString: function(timestamp) {
    if (timestamp == undefined)
      return undefined;

    return new Date(timestamp * 1000).toISOString().slice(0, 19).replace('T', ' ');
  },
  getDurationString: function(duration) {
    var sec_num = duration;
    var hours   = Math.floor(sec_num / 3600);
    var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
    var seconds = Math.floor(sec_num - (hours * 3600) - (minutes * 60));

    const padded_hours = String(hours).padStart(2, '0');
    const padded_minutes = String(minutes).padStart(2, '0');
    const padded_seconds = String(seconds).padStart(2, '0');

    return `${padded_hours}:${padded_minutes}:${padded_seconds}`;
  },
}
