// --- 1. CONFIGURAÇÃO E CONEXÃO ---
const supabaseUrl = 'https://hrmjepcajzuvopmuctet.supabase.co';
const supabaseKey = 'sb_publishable_U2zH2PnN79keKVg_MRUNUw_0H8vRYYy';
const _supabase = supabase.createClient(supabaseUrl, supabaseKey);

// Variáveis de Controle Global
let carrinho = [];
let clienteFichaId = null;
let filtroBanAtual = 'TODOS';
let relatorioAtualHTML = "";

// Sons (Certifique-se de que os arquivos existam na pasta do projeto)
const somVenda = new Audio('venda.mp3');
const somCaixa = new Audio('caixa.mp3');

// --- 2. FUNÇÕES DE BANCO DE DATA (SUPABASE) ---
async function listar(tabela) {
    const { data, error } = await _supabase.from(tabela).select('*');
    if (error) { console.error(`Erro ao listar ${tabela}:`, error); return []; }
    return data;
}

async function buscar(tabela, id) {
    const { data, error } = await _supabase.from(tabela).select('*').eq('id', id).single();
    if (error) { console.error(`Erro ao buscar na ${tabela}:`, error); return null; }
    return data;
}

async function salvar(tabela, objeto) {
    const { data, error } = await _supabase.from(tabela).upsert(objeto).select();
    if (error) { alert("Erro ao salvar: " + error.message); return null; }
    return data;
}

async function deletar(tabela, id) {
    const { error } = await _supabase.from(tabela).delete().eq('id', id);
    if (error) { alert("Erro ao excluir: " + error.message); return false; }
    return true;
}

// Auxiliar para converter data PT-BR para objeto Date
function parseDataBR(s) {
    if (!s) return new Date();
    const [d, h] = s.split(', ');
    const [dia, mes, ano] = d.split('/');
    return new Date(`${ano}-${mes}-${dia}T${h || '00:00:00'}`);
}

// --- 3. NAVEGAÇÃO E INTERFACE ---
function ir(aba, el) {
    document.querySelectorAll('.aba').forEach(a => a.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
    document.getElementById('aba-' + aba).classList.add('active');
    el.classList.add('active');
    window.scrollTo(0, 0);

    if (aba === 'vendas') {
        somCaixa.currentTime = 0;
        somCaixa.play().catch(e => console.log("Som aguardando interação"));
        atualizarDataAtualPDV();
    }
    renderizarTudo();
}

function atualizarDataAtualPDV() {
    const agora = new Date().toLocaleString('pt-BR');
    const el = document.getElementById('data-atual');
    if (el) el.innerText = agora;
}

// --- 4. RENDERIZAÇÃO PRINCIPAL ---
async function renderizarTudo() {
    const prods = await listar("estoque");
    const pessa = await listar("pessoas");
    const hists = await listar("historico");

    // Ordenações
    prods.sort((a, b) => a.nome.localeCompare(b.nome));
    pessa.sort((a, b) => a.nome.localeCompare(b.nome));

    // Filtros de busca
    const termoPessoa = document.getElementById('busca-pessoa').value.toUpperCase();
    const pessoasFiltradas = pessa.filter(p => p.nome.includes(termoPessoa));

    const termoBandeja = document.getElementById('busca-bandeja').value.toUpperCase();
    const bandejaFiltrada = pessa.filter(p => {
        const matchesSearch = p.tipo === 'ALUNO' && p.bandeja === 'SIM' && p.nome.includes(termoBandeja);
        const matchesPeriodo = filtroBanAtual === 'TODOS' || p.periodo === filtroBanAtual;
        return matchesSearch && matchesPeriodo;
    });

    // Renderizar Grid de Produtos (PDV)
    document.getElementById('pdv-grid').innerHTML = prods.filter(p => p.qtd > 0).map(p => `
        <div class="btn-prod" onclick="addCar(${p.id}, '${p.sigla}', ${p.preco})">
            <div class="badge">${p.qtd}</div>
            <b>${p.sigla}</b>
            <span>R$ ${p.preco.toFixed(2)}</span>
        </div>
    `).join('');

    // Renderizar Tabela de Pessoas
    document.getElementById('tab-p').innerHTML = pessoasFiltradas.map(p => `
        <tr>
            <td onclick="abrirExtrato(${p.id})"><b>${p.nome}</b><br><small>${p.periodo} | ${p.tel || ''}</small></td>
            <td style="color:${p.divida > 0 ? 'var(--danger)' : 'var(--success)'}; font-weight:bold">R$ ${(-p.divida).toFixed(2)}</td>
            <td style="display:flex; gap:5px">
                <button class="btn btn-sm btn-pago" onclick="abrirCobranca(${p.id})">$</button>
                <button class="btn btn-sm" style="background:var(--info); color:white" onclick="abrirModalPessoa(${p.id})">✎</button>
            </td>
        </tr>
    `).join('');

    // Renderizar Estoque
    document.getElementById('tab-estoque').innerHTML = prods.map(p => `
        <tr>
            <td><b>${p.sigla}</b><br><small>${p.nome}</small></td>
            <td>${p.qtd}</td>
            <td>
                <button class="btn btn-sm btn-pago" onclick="abrirModalProd(${p.id})">✎</button>
                <button class="btn btn-sm" style="background:var(--danger); color:white" onclick="confirmarDeletar('estoque', ${p.id})">X</button>
            </td>
        </tr>
    `).join('');

    // Renderizar Bandeja
    document.getElementById('lista-alunos-ban').innerHTML = bandejaFiltrada.map(a => `
        <div style="background:var(--card); padding:12px; margin:5px; border-radius:10px; display:flex; justify-content:space-between; border:1px solid #334155">
            <span>${a.nome} (${a.periodo})</span>
            <input type="checkbox" class="chk-ban" style="width:25px; height:25px" data-id="${a.id}">
        </div>
    `).join('');

    // Select de Clientes no PDV
    document.getElementById('sel-pessoa').innerHTML = '<option value="0">👤 CLIENTE AVULSO</option>' + 
        pessa.filter(p => p.tipo !== 'ALUNO').map(p => `<option value="${p.id}">${p.nome}</option>`).join('');

    carregarResumoFinanceiro();
}

// --- 5. LÓGICA DO CARRINHO E VENDA ---
function addCar(id, sigla, preco) {
    carrinho.push({ id, sigla, preco });
    attResumo();
}

function attResumo() {
    let t = 0;
    document.getElementById('lista-car').innerHTML = carrinho.map((c, i) => {
        t += c.preco;
        return `<div class="item-car"><span>${c.sigla}</span><b>R$ ${c.preco.toFixed(2)} <i class="fas fa-times" onclick="carrinho.splice(${i},1);attResumo()" style="color:red; margin-left:10px; cursor:pointer"></i></b></div>`;
    }).join('');
    document.getElementById('tot-car').innerText = `R$ ${t.toFixed(2)}`;
}

async function finalizarVenda() {
    if (!carrinho.length) return alert("Carrinho vazio!");
    
    const total = carrinho.reduce((a, b) => a + b.preco, 0);
    const pag = document.getElementById('sel-pagamento').value;
    const pid = parseInt(document.getElementById('sel-pessoa').value);
    const obs = document.getElementById('obs-venda').value;
    
    // Data (Retroativa ou Atual)
    const dataInput = document.getElementById('venda-data-manual')?.value;
    const dataFinal = dataInput ? new Date(dataInput).toLocaleString('pt-BR') : new Date().toLocaleString('pt-BR');

    let cliente = { nome: "AVULSO", divida: 0 };
    if (pid !== 0) {
        cliente = await buscar("pessoas", pid);
        if (!cliente) return alert("Cliente não encontrado!");
    }

    if (pag === 'FIADO' && pid === 0) return alert("Selecione um cliente para fiado!");

    // Processar itens (Estoque)
    for (let item of carrinho) {
        const prod = await buscar("estoque", item.id);
        if (prod) {
            await salvar("estoque", { ...prod, qtd: prod.qtd - 1 });
        }
    }

    // Processar Dívida
    if (pag === 'FIADO') {
        await salvar("pessoas", { ...cliente, divida: (cliente.divida || 0) + total });
    }

    // Registrar Histórico
    await salvar("historico", {
        data: dataFinal,
        total: total,
        tipo: `${pag}: ${cliente.nome} (${carrinho.map(c => c.sigla).join(',')})`,
        clienteId: pid !== 0 ? pid : null,
        obs: obs
    });

    somVenda.play().catch(e => console.log("Erro som"));
    alert("Venda Finalizada!");

    // Resetar
    carrinho = [];
    document.getElementById('obs-venda').value = "";
    if (document.getElementById('venda-data-manual')) document.getElementById('venda-data-manual').value = "";
    renderizarTudo();
}

// --- 6. RESUMO E RELATÓRIOS ---
async function carregarResumoFinanceiro() {
    const hists = await listar("historico");
    const pessoas = await listar("pessoas");

    let totais = { VENDAS: 0, PAGAMENTOS: 0, FIADO: 0, PIX: 0, DINHEIRO: 0, DEBITO: 0, CREDITO: 0, BANDEJA: 0 };

    hists.forEach(h => {
        const tipoBase = h.tipo.split(':')[0];
        if (tipoBase === 'PAGAMENTO' || tipoBase === 'CREDITO') {
            totais.PAGAMENTOS += h.total;
        } else {
            totais.VENDAS += h.total;
        }
        if (totais.hasOwnProperty(tipoBase)) totais[tipoBase] += h.total;
    });

    let dividaTotal = pessoas.reduce((acc, p) => acc + (p.divida > 0 ? p.divida : 0), 0);

    const html = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div style="background: #020617; padding: 10px; border-radius: 8px;">
                <small>TOTAL VENDAS</small>
                <h3 style="color: var(--success); margin: 5px 0;">R$ ${totais.VENDAS.toFixed(2)}</h3>
            </div>
            <div style="background: #020617; padding: 10px; border-radius: 8px;">
                <small>TOTAL PAGAMENTOS</small>
                <h3 style="color: var(--info); margin: 5px 0;">R$ ${totais.PAGAMENTOS.toFixed(2)}</h3>
            </div>
            <div style="background: #020617; padding: 10px; border-radius: 8px;">
                <small>SALDO LÍQUIDO</small>
                <h3 style="color: var(--accent); margin: 5px 0;">R$ ${(totais.VENDAS - totais.PAGAMENTOS).toFixed(2)}</h3>
            </div>
            <div style="background: #020617; padding: 10px; border-radius: 8px;">
                <small>DÍVIDAS CLIENTES</small>
                <h3 style="color: var(--danger); margin: 5px 0;">R$ ${dividaTotal.toFixed(2)}</h3>
            </div>
        </div>
        <hr style="border-color: #334155; margin: 15px 0;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.75rem;">
            <div>💵 DINHEIRO: <strong>R$ ${totais.DINHEIRO.toFixed(2)}</strong></div>
            <div>💎 PIX: <strong>R$ ${totais.PIX.toFixed(2)}</strong></div>
            <div>💳 DÉBITO: <strong>R$ ${totais.DEBITO.toFixed(2)}</strong></div>
            <div>💳 CRÉDITO: <strong>R$ ${totais.CREDITO.toFixed(2)}</strong></div>
            <div>📝 FIADO: <strong>R$ ${totais.FIADO.toFixed(2)}</strong></div>
            <div>🍽️ BANDEJA: <strong>R$ ${totais.BANDEJA.toFixed(2)}</strong></div>
        </div>
    `;
    document.getElementById('resumo-financeiro').innerHTML = html;
}

// --- 7. EXTRATOS E COBRANÇA ---
async function abrirCobranca(id) {
    clienteFichaId = id;
    const p = await buscar("pessoas", id);
    const saldoReal = -p.divida;
    
    document.getElementById('info-pagar').innerHTML = `
        <b>Cliente:</b> ${p.nome}<br>
        <b>Status:</b> <span style="color:${saldoReal < 0 ? 'var(--danger)' : 'var(--success)'}">
        ${saldoReal < 0 ? 'Em Débito' : 'Crédito'} de R$ ${Math.abs(saldoReal).toFixed(2)}</span>
    `;
    document.getElementById('val-pago').value = p.divida > 0 ? p.divida : "";
    document.getElementById('modal-pagar').style.display = 'block';
}

async function processarPagamento(tipo) {
    const v = parseFloat(document.getElementById('val-pago').value);
    if (isNaN(v) || v <= 0) return alert("Insira um valor válido!");
    
    const p = await buscar("pessoas", clienteFichaId);
    await salvar("pessoas", { ...p, divida: p.divida - v });
    
    await salvar("historico", {
        data: new Date().toLocaleString('pt-BR'),
        total: v,
        tipo: `${tipo}: ${p.nome}`,
        clienteId: p.id,
        obs: tipo === 'CREDITO' ? "Crédito antecipado" : "Recebimento de conta"
    });

    fecharModal('modal-pagar');
    renderizarTudo();
    alert("Registrado com sucesso!");
}

// --- 8. INICIALIZAÇÃO ---
window.onload = async () => {
    // Verificar autenticação simples (sessionStorage)
    if (sessionStorage.getItem('autenticado') === 'true') {
        document.getElementById('tela-login').style.display = 'none';
        document.getElementById('main-app').style.display = 'block';
        atualizarDataAtualPDV();
        renderizarTudo();
    }
};

// Funções de Modal e UI auxiliares
function fecharModal(m) { document.getElementById(m).style.display = 'none'; }
function toggleBanField() { 
    const tipo = document.getElementById('p-tipo').value;
    document.getElementById('p-ban-box').style.display = (tipo === 'ALUNO') ? 'block' : 'none'; 
}
async function confirmarDeletar(tabela, id) {
    if (confirm("Tem certeza que deseja excluir?")) {
        await deletar(tabela, id);
        renderizarTudo();
    }
}
