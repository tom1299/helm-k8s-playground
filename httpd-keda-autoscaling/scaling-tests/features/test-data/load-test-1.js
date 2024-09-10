import http from 'k6/http';

export const options = {
  scenarios: {
    constant_request_rate: {
      executor: 'constant-arrival-rate',
      rate: 100,
      timeUnit: '1m',
      duration: '90s',
      preAllocatedVUs: 100,
      maxVUs: 200,
    },
  },
};

export default function () {
  http.get('http://httpd.httpd-autoscaling.svc.cluster.local:8888');
}