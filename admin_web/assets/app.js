const element = id => document.getElementById(id);
const format = n => n == null ? '—' : new Intl.NumberFormat('ja-JP').format(n);
function ranking(id, rows) {
  element(id).replaceChildren();
  if (!rows.length) { const empty = document.createElement('li'); empty.textContent = '登録データはありません'; element(id).append(empty); return; }
  const max = Math.max(1, ...rows.map(row => row.count));
  rows.forEach((row, index) => {
    const li = document.createElement('li');
    const rank = document.createElement('span'); rank.className = 'rank'; rank.textContent = String(index + 1).padStart(2, '0');
    const details = document.createElement('div'); details.className = 'details';
    const name = document.createElement('strong'); name.textContent = row.name || '名称未取得';
    const meter = document.createElement('progress'); meter.max = max; meter.value = row.count; meter.setAttribute('aria-label', `${row.name}の登録数`);
    details.append(name, meter);
    const count = document.createElement('span'); count.className = 'count'; count.textContent = `${format(row.count)} 語`;
    li.append(rank, details, count); element(id).append(li);
  });
}
async function refresh() {
  element('refresh').disabled = true;
  element('status').textContent = '統計を取得しています…';
  try {
    const response = await fetch('/api/statistics', {cache: 'no-store'});
    if (!response.ok) throw new Error('統計を取得できませんでした。再読み込みしてください。');
    const data = await response.json(); const c = data.counts;
    element('cards').replaceChildren();
    [['登録ワード', c.words, '削除済みを除く'], ['導入サーバー', data.current_guilds, '現在のBot導入先'], ['参加ユーザー', c.participants, 'ゲーム参加記録のユニーク数'], ['ゲーム稼働サーバー', c.playing_guilds, 'ゲーム開始中のサーバー'], ['ワード登録ユーザー', c.contributors, '現在のワード登録者'], ['削除済みワード', c.deleted_words, '論理削除された登録データ']].forEach(([label, value, note]) => {
      const card = document.createElement('article');
      const title = document.createElement('h2'); title.textContent = label;
      const number = document.createElement('b'); number.textContent = format(value);
      const sub = document.createElement('p'); sub.textContent = note;
      card.append(title, number, sub); element('cards').append(card);
    });
    ranking('users', data.users); ranking('guilds', data.guilds);
    element('status').textContent = `集計日時 ${new Date(data.updated_at).toLocaleString('ja-JP', {timeZone: 'Asia/Tokyo'})} JST${data.discord_status !== 'ok' ? ' · Discord情報を取得できません。導入サーバー数は未取得です。' : ''}`;
  } catch (error) { element('status').textContent = error.message; }
  finally { element('refresh').disabled = false; }
}
element('refresh').addEventListener('click', refresh);
refresh();

function textNode(tag, text, className) {
  const node = document.createElement(tag); node.textContent = text;
  if (className) node.className = className;
  return node;
}
let moderationData = null;
let targetOptions = new Map();

function updateTargetOptions(clearValue = false) {
  const target = element('ng-target').value;
  const action = element('ng-action').value;
  const data = moderationData;
  targetOptions = new Map();
  element('ng-options').replaceChildren();
  if (clearValue) element('ng-value').value = '';
  element('ng-submit').textContent = action === 'block' ? '登録' : '解除';
  if (!data) return;
  let options;
  if (target === 'word') {
    options = action === 'unblock' ? data.ng_words : [...new Set([...(data.word_candidates || []), ...data.ng_words])];
    options = options.map(word => ({label:word, value:word}));
  } else {
    const blocked = target === 'guild' ? data.blocked_guilds : data.blocked_users;
    const candidates = target === 'guild' ? (data.guild_candidates || []) : (data.user_candidates || []);
    const rows = action === 'unblock' ? blocked : candidates.filter(row => !blocked.some(entry => entry.id === row.id));
    options = rows.map(row => ({label:`${row.name || '名称未取得'} / ${row.id}`, value:row.id}));
  }
  options.sort((left, right) => left.label.localeCompare(right.label, 'ja'));
  options.forEach(({label, value}) => {
    targetOptions.set(label, value);
    const option = document.createElement('option'); option.value = label;
    element('ng-options').append(option);
  });
  element('ng-help').textContent = target === 'word'
    ? 'NGワード・登録済みワード（最大1,000種類）から選択、または新しいワードを直接入力できます。解除の候補は現在のNGワードです。'
    : '名前 / IDから選択できます。登録候補はDBに記録されたサーバー・ゲーム参加ユーザー、解除候補は現在のNG設定です。候補にない対象は数字のDiscord IDを入力してください。';
}

async function refreshModeration() {
  element('ng-status').textContent = 'NG情報を取得しています…';
  try {
    const response = await fetch('/api/moderation', {cache: 'no-store'});
    if (!response.ok) throw new Error('NG情報を取得できませんでした。設定・DBの状態を確認してください。');
    const data = await response.json();
    moderationData = data;
    updateTargetOptions();
    element('ng-counts').replaceChildren(textNode('p', `NGユーザー ${format(data.blocked_users.length)}件 ／ NGサーバー ${format(data.blocked_guilds.length)}件 ／ NGワード ${format(data.ng_words.length)}件 ／ 通報 ${format(data.report_counts.total)}件（通知未記録 ${format(data.report_counts.unnotified)}件）`));
    [['blocked-users', data.blocked_users], ['blocked-guilds', data.blocked_guilds]].forEach(([id, rows]) => {
      element(id).replaceChildren(...(rows.length ? rows.map(row => { const li = textNode('li', `${row.name || '名称未取得'} · ID: ${row.id}`); li.append(removeButton(id === 'blocked-users' ? 'user' : 'guild', row.id)); return li; }) : [textNode('li', 'NG設定はありません')]));
    });
    element('ng-words').replaceChildren(...(data.ng_words.length ? data.ng_words.map(word => { const node = textNode('span', word, 'ng-word'); node.append(removeButton('word', word)); return node; }) : [textNode('p', 'NGワード設定はありません')]));
    element('words-captured').textContent = `Botと共有する現在の設定です。最終更新 ${new Date(data.words_captured_at).toLocaleString('ja-JP', {timeZone:'Asia/Tokyo'})} JST。表記は正規化後、部分一致で判定します。`;
    element('reports').replaceChildren(...(data.reports.length ? data.reports.map(report => {
      const article = document.createElement('article'); article.className = 'report';
      article.append(textNode('h4', report.word_snapshot), textNode('p', report.reason || '理由の記入なし'),
        textNode('p', `${report.guild_name || '名称未取得'} · サーバーID: ${report.guild_id} · チャンネルID: ${report.channel_id}`),
        textNode('p', `登録者記録: ${report.owner_snapshot || '未取得'} ／ 通報者ID: ${report.reporter_id}`),
        textNode('p', `${report.created_at} JST · ${report.notified ? '通知済み' : '通知未記録'} · ワードID: ${report.word_id} · 通報ID: ${report.report_id}`));
      return article;
    }) : [textNode('p', '通報はありません')]));
    element('ng-status').textContent = `取得日時 ${new Date(data.updated_at).toLocaleString('ja-JP', {timeZone:'Asia/Tokyo'})} JST`;
  } catch (error) {
    ['ng-counts', 'blocked-users', 'blocked-guilds', 'ng-words', 'words-captured', 'reports'].forEach(id => element(id).replaceChildren());
    moderationData = null; targetOptions.clear(); element('ng-options').replaceChildren();
    element('ng-status').textContent = error.message;
  }
}
element('refresh').addEventListener('click', refreshModeration);
refreshModeration();

let changingNg = false;
function removeButton(target, value) {
  const button = textNode('button', '解除'); button.type = 'button'; button.className = 'remove-ng';
  button.addEventListener('click', () => changeNg(target, 'unblock', value)); return button;
}
async function changeNg(target, action, value) {
  if (changingNg) return;
  const label = {user:'ユーザー', guild:'サーバー', word:'ワード'}[target];
  const consequence = target === 'guild' && action === 'block' ? '\nBotが対象サーバーから退出します。解除しても自動では再参加しません。' : '';
  const rows = target === 'guild' ? [...(moderationData?.guild_candidates || []), ...(moderationData?.blocked_guilds || [])] : [...(moderationData?.user_candidates || []), ...(moderationData?.blocked_users || [])];
  const selected = rows.find(row => row.id === value);
  const description = target !== 'word' && selected ? `${selected.name || '名称未取得'} / ${value}` : value;
  if (!window.confirm(`${label}「${description}」を${action === 'block' ? 'NG登録' : 'NG解除'}しますか？${consequence}`)) return;
  changingNg = true; element('ng-submit').disabled = true; element('ng-result').textContent = '更新しています…';
  try {
    const csrf = await fetch('/api/csrf', {cache:'no-store'});
    if (!csrf.ok) throw new Error('管理者の認証を確認してください。');
    const {token} = await csrf.json();
    const response = await fetch('/api/moderation', {method:'POST', headers:{'Content-Type':'application/json', 'X-CSRF-Token':token}, body:JSON.stringify({target, action, value})});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '設定を更新できませんでした。');
    element('ng-result').textContent = result.message;
    element('ng-value').value = '';
  } catch (error) { element('ng-result').textContent = error.message; }
  finally { changingNg = false; element('ng-submit').disabled = false; await refreshModeration(); }
}
element('ng-form').addEventListener('submit', event => {
  event.preventDefault();
  const target = element('ng-target').value;
  const input = element('ng-value').value.trim();
  const value = target === 'word' ? input : (targetOptions.get(input) || input);
  if (target !== 'word' && !/^[0-9]+$/.test(value)) {
    element('ng-result').textContent = '候補から選択するか、数字のDiscord IDを入力してください。'; return;
  }
  changeNg(target, element('ng-action').value, value);
});

['ng-target', 'ng-action'].forEach(id => element(id).addEventListener('change', () => updateTargetOptions(true)));

let importingCsv = false;
element('csv-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (importingCsv) return;
  const file = element('csv-file').files[0];
  if (!file || !file.name.toLowerCase().endsWith('.csv') || file.size > 1024 * 1024) {
    element('csv-result').textContent = '1MB以下の.csvファイルを選択してください。'; return;
  }
  importingCsv = true; element('csv-submit').disabled = true;
  element('csv-result').textContent = 'CSVを検証しています…';
  try {
    const csrfResponse = await fetch('/api/csrf', {cache:'no-store'});
    if (!csrfResponse.ok) throw new Error('管理者の認証を確認してください。');
    const {token} = await csrfResponse.json();
    const bytes = await file.arrayBuffer();
    const options = {method:'POST', headers:{'Content-Type':'text/csv','X-CSRF-Token':token,'X-Upload-Filename':encodeURIComponent(file.name)}, body:bytes};
    const previewResponse = await fetch('/api/ng-words/csv/preview', options);
    const preview = await previewResponse.json();
    if (!previewResponse.ok) throw new Error(preview.error || 'CSVを読み取れませんでした。');
    const message = `${file.name}\nデータ ${preview.rows}行／重複を除いたワード ${preview.unique}件\n新規追加予定 ${preview.added}件／登録済み ${preview.existing}件\n\n先頭20件：\n${preview.preview.join('\n')}\n\n既存設定へ追加しますか？`;
    if (!window.confirm(message)) { element('csv-result').textContent = '取り込みをキャンセルしました。'; return; }
    const response = await fetch('/api/ng-words/csv/import', options);
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'CSVを追加できませんでした。');
    element('csv-result').textContent = `追加 ${result.added}件、登録済み ${result.existing}件。NGワード合計 ${result.total}件になりました。`;
    element('csv-file').value = '';
  } catch (error) { element('csv-result').textContent = error.message; }
  finally { importingCsv = false; element('csv-submit').disabled = false; await refreshModeration(); }
});
