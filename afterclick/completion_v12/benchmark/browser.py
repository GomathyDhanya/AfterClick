"""Native action gateway over ordinary visible browser state; no evaluator/world access."""

import json
import time


class Browser:
    def __init__(self, page, origin, application):
        self.page = page
        self.history = []
        self.network = []

        def outgoing(request):
            if request.method == "POST" and request.url == origin + "/api/v12/act":
                self.network.append(
                    dict(
                        kind="browser.request",
                        wall=time.time(),
                        mono=time.monotonic(),
                        body=request.post_data_json,
                    )
                )

        page.on("request", outgoing)
        page.set_default_timeout(15000)
        page.goto(origin + ("/workflow" if application == "flowboard" else "/"))
        page.wait_for_function("current!==null")
        # Align an initial quiescent client cut before the environment clock starts.
        # Only read-only refreshes have occurred. No live business state is reset.
        page.evaluate("clearInterval(pollingTimer); pollingTimer=null")
        page.wait_for_function("activeRefreshes===0 && !busy")
        page.evaluate("refreshSerial=visibleSerial=0")

    def client_cut(self):
        return self.page.evaluate("""({busy, selected, lastResult, activeRefreshes,
            refreshSerial, visibleSerial, polling:pollingTimer!==null,
            scroll:[scrollX,scrollY], viewport:[innerWidth,innerHeight],
            focus:document.activeElement.tagName,
            choices:[...document.querySelectorAll('select')].map(x=>[x.dataset.choice,x.value]),
            recordText:document.querySelector('#records').innerText,
            document_html:document.documentElement.outerHTML})""")

    def start_polling(self):
        self.page.evaluate("""if(pollingTimer!==null)throw Error('Polling already running');
            pollingTimer=setInterval(()=>{if(!busy)refresh()},350)""")

    def observe(self):
        return json.loads(self.page.locator("#public").inner_text())

    def act(self, identifier, value=""):
        begin = time.time()
        self.page.wait_for_function("!busy")
        serial = self.page.evaluate("actionSerial")
        if identifier.startswith("w"):
            self.page.locator(f'[data-choice="{identifier}"]').select_option(value)
        # Native keyboard activation avoids a pointer becoming stale while the
        # viewport scrolls through asynchronously changing service feedback.
        self.page.locator(f'button[data-op="{identifier}"]').press("Enter")
        self.page.wait_for_function("completedSerial > " + str(serial) + " && !busy")
        result = self.page.evaluate("lastResult")
        row = dict(
            id=identifier, value=value, result=result, start_wall=begin, end_wall=time.time()
        )
        self.history.append(row)
        return result
