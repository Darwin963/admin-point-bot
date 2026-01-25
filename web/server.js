const path = require('path');
const express = require('express');
const bodyParser = require('body-parser');
const fetch = require('node-fetch');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '1mb' }));

const PORT = process.env.PORT || 3000;

app.use('/', express.static(path.join(__dirname, 'public')));

const ALLOWED_FILES = [
  'bot.py',
  'Add_points_order.js',
  'logs.js',
  'panel.js',
  'points.js',
  'top.js'
];

app.get('/api/read-file', (req, res) => {
  const file = req.query.file;
  if (!ALLOWED_FILES.includes(file)) {
    return res.status(403).json({ error: 'File not allowed' });
  }
  const filePath = path.join(__dirname, '..', file);
  require('fs').readFile(filePath, 'utf8', (err, data) => {
    if (err) return res.status(500).json({ error: 'Failed to read file' });
    res.json({ content: data });
  });
});

app.post('/api/apply-fix', (req, res) => {
  const { file, newContent } = req.body;
  if (!ALLOWED_FILES.includes(file)) {
    return res.status(403).json({ error: 'File not allowed' });
  }
  const filePath = path.join(__dirname, '..', file);
  require('fs').writeFile(filePath, newContent, 'utf8', (err) => {
    if (err) return res.status(500).json({ error: 'Failed to write file' });
    res.json({ ok: true, message: 'File updated successfully' });
  });
});

app.post('/api/fix', async (req, res) => { // eslint-disable-line no-unused-vars
  const { problem, code } = req.body || {};
  const OPENAI_KEY = process.env.OPENAI_API_KEY || null;
  const model = process.env.OPENAI_MODEL || 'gpt-4o-mini';

  if (!problem && !code) return res.status(400).json({ error: 'Provide `problem` or `code` in the JSON body.' });

  if (!OPENAI_KEY) {
    return res.json({
      ok: false,
      message: 'No OPENAI_API_KEY set. Set OPENAI_API_KEY in a .env file or environment to enable AI suggestions.',
      suggestion: 'You can run the server and enter your OpenAI API key in the .env file as OPENAI_API_KEY=sk-...'
    });
  }

  try {
    const prompt = `You are an assistant that fixes code errors. The user describes a problem and may provide code. Respond with a concise explanation of the fix, and provide the corrected code enclosed in triple backticks (```) if applicable.\n\nProblem:\n${problem || '<none provided>'}\n\nCode:\n${code || '<none provided>'}`;

    const body = {
      model: model,
      messages: [
        { role: 'system', content: 'You are a helpful assistant that provides code fixes. When providing corrected code, enclose it in triple backticks (```) for easy extraction.' },
        { role: 'user', content: prompt }
      ],
      max_tokens: 1000,
      temperature: 0.2
    };

    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_KEY}`
      },
      body: JSON.stringify(body)
    });

    if (!r.ok) {
      const errText = await r.text();
      return res.status(502).json({ ok: false, error: 'OpenAI API error', detail: errText });
    }

    const data = await r.json();
    const assistant = data.choices && data.choices[0] && data.choices[0].message ? data.choices[0].message.content : null;
    return res.json({ ok: true, reply: assistant });
  } catch (err) {
    return res.status(500).json({ ok: false, error: String(err) });
  }
);

app.listen(PORT, () => {
  console.log(`AI fixer web running on http://localhost:${PORT}`);
});
