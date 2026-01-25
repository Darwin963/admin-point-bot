document.getElementById('loadFile').addEventListener('click', async () => {
  const file = document.getElementById('fileSelect').value;
  if (!file) return alert('اختر ملف أولاً');
  const codeEl = document.getElementById('code');
  codeEl.value = 'جارٍ التحميل...';
  try {
    const r = await fetch(`/api/read-file?file=${encodeURIComponent(file)}`);
    const data = await r.json();
    if (r.ok) {
      codeEl.value = data.content;
    } else {
      alert('خطأ: ' + data.error);
      codeEl.value = '';
    }
  } catch (err) {
    alert('خطأ: ' + err);
    codeEl.value = '';
  }
});

document.getElementById('send').addEventListener('click', async () => {
  const problem = document.getElementById('problem').value;
  const code = document.getElementById('code').value;
  const replyEl = document.getElementById('reply');
  replyEl.textContent = 'جارٍ الاتصال بالخادم...';

  try {
    const r = await fetch('/api/fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ problem, code })
    });
    const data = await r.json();
    if (data.ok) {
      replyEl.textContent = data.reply || JSON.stringify(data, null, 2);
      document.getElementById('applyFix').style.display = 'block';
    } else {
      replyEl.textContent = data.message || data.error || JSON.stringify(data, null, 2);
      document.getElementById('applyFix').style.display = 'none';
    }
  } catch (err) {
    replyEl.textContent = String(err);
    document.getElementById('applyFix').style.display = 'none';
  }
});

document.getElementById('applyFix').addEventListener('click', async () => {
  const file = document.getElementById('fileSelect').value;
  if (!file) {
    alert('اختر ملف أولاً لتطبيق الإصلاح عليه.');
    return;
  }
  let newContent = document.getElementById('reply').textContent;
  if (!newContent || newContent === 'لم يتم إرسال شيء بعد.' || newContent.startsWith('جارٍ')) {
    alert('لا يوجد رد للتطبيق.');
    return;
  }

  // استخراج الكود من الرد إذا كان محاطًا بـ ```
  const codeMatch = newContent.match(/```(?:\w+)?\n?([\s\S]*?)```/);
  if (codeMatch) {
    newContent = codeMatch[1].trim();
  }

  if (!confirm('هل أنت متأكد من تطبيق الإصلاح؟ سيستبدل محتوى الملف بالكود المستخرج.')) return;

  try {
    const r = await fetch('/api/apply-fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file, newContent })
    });
    const data = await r.json();
    if (data.ok) {
      alert('تم تطبيق الإصلاح بنجاح.');
    } else {
      alert('خطأ: ' + data.error);
    }
  } catch (err) {
    alert('خطأ: ' + err);
  }
});
