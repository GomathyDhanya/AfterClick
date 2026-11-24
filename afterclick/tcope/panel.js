(() => {
  const panel = document.createElement('section');
  panel.id = 'controlled-service';
  panel.style.cssText = 'margin:20px 20px 20px 290px;position:relative;padding:20px;border:2px solid #64748b;background:#fff;color:#111;max-width:1100px';
  panel.innerHTML = '<h2>Controlled synthetic service</h2><pre id="service-state"></pre><div id="service-actions"></div><p id="service-error"></p>';
  document.body.append(panel);
  let busy=false, buttonsBuilt=false, lastNonce=window.tcBootstrap?.last_nonce ?? null;
  window.tcHold=!!window.tcBootstrap;
  window.tcClientCheckpoint={last_nonce:lastNonce};
  function render(state) {
    const {available_actions,...visible}=state;
    document.getElementById('service-state').textContent=JSON.stringify(visible,null,2);
    if (!buttonsBuilt) {
      for (const name of available_actions) {
        const button=document.createElement('button');button.textContent=name;
        button.onclick=async()=>{
          if (busy) return;
          busy=true;for(const b of panel.querySelectorAll('button')) b.disabled=true;
          try {
            if(name==='Wait for update') await new Promise(resolve=>setTimeout(resolve,500));
            else {
              const nonce=name==='Retry resource'&&lastNonce?lastNonce:crypto.randomUUID();
              if(name==='Capture resource') lastNonce=nonce;
              window.tcClientCheckpoint.last_nonce=lastNonce;
              const reply=await fetch('/api/tcope/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,nonce})});
              if(!reply.ok)throw new Error('Service request failed; verify state before retrying.');
            }
            document.getElementById('service-error').textContent='';await refresh();
          } catch(error){document.getElementById('service-error').textContent=String(error);}
          finally{busy=false;for(const b of panel.querySelectorAll('button'))b.disabled=false;}
        };
        document.getElementById('service-actions').append(button);
      }
      buttonsBuilt=true;
    }
  }
  async function refresh(){const reply=await fetch('/api/tcope/state');const state=await reply.json();if(!window.tcHold)render(state);}
  if(window.tcBootstrap)render(window.tcBootstrap.public_state);else refresh();
  setInterval(()=>{if(!busy&&!window.tcHold)refresh().catch(()=>{});},100);
})();
