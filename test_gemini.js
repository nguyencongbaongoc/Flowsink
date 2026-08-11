import { GoogleGenerativeAI } from '@google/generative-ai';
import fs from 'fs';

const envContent = fs.readFileSync('./.env.local', 'utf8');
const match = envContent.match(/VITE_GEMINI_API_KEY=(.*)/);
const apiKey = match ? match[1].trim() : '';

if (!apiKey) {
  console.error('ERROR: No API key found in .env.local. Please set VITE_GEMINI_API_KEY.');
  process.exit(1);
}

if (!apiKey.startsWith('AIzaSy') && !apiKey.startsWith('AQ.')) {
  console.error('ERROR: The key in .env.local must be a valid Gemini API Key (starts with AIzaSy... or AQ....)');
  console.error('Get an API key at: https://aistudio.google.com/app/apikey');
  process.exit(1);
}

console.log('Testing with key prefix:', apiKey.substring(0, 10) + '...');

const genAI = new GoogleGenerativeAI(apiKey);
const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

try {
  const result = await model.generateContent('Say hello');
  console.log('SUCCESS:', result.response.text());
} catch (err) {
  console.error('ERROR status:', err.status);
  console.error('ERROR message:', err.message);
  if (err.status === 401) {
    console.error('Authentication failed. The API key is invalid or expired.');
    console.error('Please get a new API key at: https://aistudio.google.com/app/apikey');
  }
}