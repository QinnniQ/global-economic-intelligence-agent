/** Open one GitHub issue for a failing production monitor and close it on recovery. */
const [state] = process.argv.slice(2);
if (!['failure', 'success'].includes(state)) throw new Error('Pass failure or success');
const repository = process.env.GITHUB_REPOSITORY;
const token = process.env.GH_TOKEN;
const runId = process.env.GITHUB_RUN_ID;
if (!repository || !token || !runId) throw new Error('GitHub workflow environment is required');
const title = process.env.MONITOR_TITLE || '[Monitor] Production data probe failing';
const description = process.env.MONITOR_DESCRIPTION || 'The scheduled public API probe failed.';
const runUrl = `https://github.com/${repository}/actions/runs/${runId}`;
const api = `https://api.github.com/repos/${repository}`;
const headers = { authorization: `Bearer ${token}`, accept: 'application/vnd.github+json', 'content-type': 'application/json', 'x-github-api-version': '2022-11-28' };
async function request(path, method = 'GET', body) {
  const response = await fetch(`${api}${path}`, { method, headers, body: body && JSON.stringify(body) });
  if (!response.ok) throw new Error(`GitHub issue API returned ${response.status}`);
  return response.json();
}
const issues = await request('/issues?state=all&per_page=100');
let issue = issues.find(item => item.title === title && !item.pull_request);
if (state === 'failure') {
  if (!issue) issue = await request('/issues', 'POST', { title, body: `${description} Check the [workflow run](${runUrl}) for details.` });
  else {
    if (issue.state === 'closed') await request(`/issues/${issue.number}`, 'PATCH', { state: 'open' });
    await request(`/issues/${issue.number}/comments`, 'POST', { body: `${description} [Workflow run](${runUrl}).` });
  }
} else if (issue?.state === 'open') {
  await request(`/issues/${issue.number}/comments`, 'POST', { body: `The monitor recovered: [workflow run](${runUrl}).` });
  await request(`/issues/${issue.number}`, 'PATCH', { state: 'closed' });
}
