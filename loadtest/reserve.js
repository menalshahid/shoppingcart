import http from 'k6/http';
import { Counter } from 'k6/metrics';

const created = new Counter('reserve_201');
const soldOut = new Counter('reserve_409_sold_out');
const other = new Counter('reserve_other');

export const options = {
  scenarios: {
    burst: {
      executor: 'shared-iterations',
      vus: 2000,
      iterations: 2000,
      maxDuration: '60s',
    },
  },
  thresholds: {
    reserve_201: ['count==100'],
    reserve_409_sold_out: ['count==1900'],
    reserve_other: ['count==0'],
  },
};

export default function () {
  const base = __ENV.BASE_URL || 'http://localhost:8000';
  const res = http.post(
    `${base}/drops/${__ENV.DROP_ID}/reserve`,
    null,
    { headers: { 'X-User-Id': `user-${__VU}` } }
  );

  if (res.status === 201) {
    created.add(1);
  } else if (res.status === 409 && res.body && res.body.includes('SOLD_OUT')) {
    soldOut.add(1);
  } else {
    other.add(1);
    if (__VU % 40 === 0) {
      console.log(`UNEXPECTED status=${res.status} error=${res.error} body=${String(res.body).slice(0, 150)}`);
    }
  }
}