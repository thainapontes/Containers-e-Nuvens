import http from "node:http";
const { config } = await import(process.argv[2]);
console.log(`porta = ${config.porta}`);
try {
  const s = http.createServer().listen(config.porta, () => { console.log(`escutando em ${config.porta}`); s.close(); });
} catch (e) { console.log(`ERRO: ${e.code} ${e.message}`); }
