// Course Advisor chat: asks a few questions, then asks the server for matching tracks.
(function () {
    const panel = document.getElementById('advisorPanel');
    if (!panel) return;
    const launcher = document.getElementById('advisorLauncher');
    const body = document.getElementById('advisorBody');
    const input = document.getElementById('advisorInput');
    const logo = panel.querySelector('.advisor-avatar').getAttribute('src');

    const STEPS = [
        { key: 'interests', max: 2, text: "Hi! I'm the MS Academy course advisor. What do you enjoy most? Pick up to two.",
          options: [
            ['protect', 'Protecting systems & stopping hackers'], ['data', 'Numbers & finding insights'],
            ['build', 'Building websites & apps'], ['design', 'Visual design & creativity'],
            ['people', 'Understanding users'], ['marketing', 'Writing, social media & brands'],
            ['business', 'Running my own business'], ['logic', 'Logic & puzzles'] ] },
        { key: 'goal', text: "Nice. What's your main goal right now?",
          options: [ ['job', 'Land a tech job'], ['freelance', 'Freelance / remote income'],
            ['business', 'Grow my own business'], ['switch', 'Switch careers into tech'], ['explore', 'Just exploring'] ] },
        { key: 'experience', text: 'How much tech experience do you have?',
          options: [ ['none', 'Complete beginner'], ['some', 'I know some basics'], ['tech', 'I already work in tech'] ] },
        { key: 'laptop', text: 'Do you have a laptop you can learn on?',
          options: [ ['yes', 'Yes'], ['no', 'Not yet, only a phone'] ] },
        { key: 'about', free: true,
          text: "Last one: in your own words, what would you love to do? (Optional. E.g. \"I want to design logos for small businesses\")" },
    ];

    let step = 0;
    let answers = {};
    let started = false;

    function scrollDown() { body.scrollTop = body.scrollHeight; }

    function bubble(text, who) {
        const row = document.createElement('div');
        row.className = 'advisor-msg advisor-msg--' + who;
        if (who === 'bot') {
            const img = document.createElement('img');
            img.src = logo; img.alt = ''; img.className = 'advisor-msg-avatar';
            row.appendChild(img);
        }
        const p = document.createElement('p');
        p.textContent = text;
        row.appendChild(p);
        body.appendChild(row);
        scrollDown();
        return row;
    }

    function typing() {
        const row = bubble('…', 'bot');
        row.classList.add('advisor-typing');
        return row;
    }

    function ask() {
        const s = STEPS[step];
        const t = typing();
        setTimeout(() => {
            t.remove();
            bubble(s.text, 'bot');
            renderInput(s);
        }, 450);
    }

    function renderInput(s) {
        input.innerHTML = '';
        if (s.free) {
            const form = document.createElement('form');
            form.className = 'advisor-free';
            const field = document.createElement('input');
            field.type = 'text'; field.maxLength = 600; field.placeholder = 'Type here…';
            field.setAttribute('aria-label', 'Tell the advisor about yourself');
            const send = document.createElement('button');
            send.type = 'submit'; send.className = 'cta-btn'; send.textContent = 'Get advice';
            const skip = document.createElement('button');
            skip.type = 'button'; skip.className = 'advisor-skip'; skip.textContent = 'Skip';
            form.append(field, send, skip);
            input.appendChild(form);
            field.focus();
            form.addEventListener('submit', (e) => { e.preventDefault(); answer(s, field.value.trim()); });
            skip.addEventListener('click', () => answer(s, ''));
            return;
        }
        const wrap = document.createElement('div');
        wrap.className = 'advisor-chips';
        const picked = new Set();
        s.options.forEach(([value, label]) => {
            const chip = document.createElement('button');
            chip.type = 'button'; chip.className = 'advisor-chip'; chip.textContent = label;
            chip.addEventListener('click', () => {
                if (!s.max) return answer(s, value, label);
                if (picked.has(value)) { picked.delete(value); chip.classList.remove('is-picked'); }
                else if (picked.size < s.max) { picked.add(value); chip.classList.add('is-picked'); }
                done.disabled = picked.size === 0;
            });
            wrap.appendChild(chip);
        });
        input.appendChild(wrap);
        let done;
        if (s.max) {
            done = document.createElement('button');
            done.type = 'button'; done.className = 'cta-btn advisor-next'; done.textContent = 'Next'; done.disabled = true;
            done.addEventListener('click', () => {
                const labels = s.options.filter(([v]) => picked.has(v)).map(([, l]) => l);
                answer(s, Array.from(picked), labels.join(' + '));
            });
            input.appendChild(done);
        }
    }

    function answer(s, value, label) {
        answers[s.key] = value;
        if (s.free) { if (value) bubble(value, 'user'); }
        else bubble(label || value, 'user');
        input.innerHTML = '';
        step += 1;
        if (step < STEPS.length) ask(); else submit();
    }

    async function submit() {
        const t = typing();
        try {
            const res = await fetch(panel.dataset.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify({
                    interests: answers.interests || [], goal: answers.goal, experience: answers.experience,
                    laptop: answers.laptop !== 'no', about: answers.about || '',
                }),
            });
            if (!res.ok) throw new Error(res.status === 429 ? 'busy' : 'error');
            const data = await res.json();
            t.remove();
            showResults(data);
        } catch (err) {
            t.remove();
            bubble(err.message === 'busy'
                ? "I'm getting a lot of questions right now. Please try again in a minute."
                : "Sorry, I couldn't reach the server. Please check your connection and try again.", 'bot');
            restartButton();
        }
    }

    function showResults(data) {
        const recs = data.recommendations || [];
        if (!recs.length) {
            bubble("I couldn't find a clear match. Browse all our tracks, or tell me a bit more about what you enjoy.", 'bot');
            restartButton(true);
            return;
        }
        bubble(data.summary, 'bot');
        recs.forEach((r, i) => {
            const card = document.createElement('div');
            card.className = 'advisor-result' + (i === 0 ? ' advisor-result--top' : '');
            const head = document.createElement('div');
            head.className = 'advisor-result-head';
            const icon = document.createElement('i'); icon.className = r.icon;
            const title = document.createElement('strong'); title.textContent = r.title;
            const match = document.createElement('span'); match.className = 'advisor-match';
            match.textContent = i === 0 ? 'Best match' : r.match + '% match';
            head.append(icon, title, match);
            const meta = document.createElement('p'); meta.className = 'advisor-meta';
            meta.textContent = [r.duration, r.level].filter(Boolean).join(' · ');
            const list = document.createElement('ul');
            r.reasons.forEach((why) => { const li = document.createElement('li'); li.textContent = why; list.appendChild(li); });
            const links = document.createElement('div'); links.className = 'advisor-links';
            const view = document.createElement('a'); view.href = r.url; view.textContent = 'View syllabus';
            const apply = document.createElement('a'); apply.href = r.url + 'apply/'; apply.className = 'advisor-apply'; apply.textContent = 'Apply';
            links.append(view, apply);
            card.append(head, meta, list, links);
            body.appendChild(card);
        });
        scrollDown();
        restartButton(true);
    }

    function restartButton(showBrowse) {
        input.innerHTML = '';
        const again = document.createElement('button');
        again.type = 'button'; again.className = 'advisor-skip'; again.textContent = 'Start over';
        again.addEventListener('click', reset);
        input.appendChild(again);
        if (showBrowse) {
            const all = document.createElement('a');
            all.href = '/tracks/'; all.className = 'cta-btn cta-btn--outline advisor-browse'; all.textContent = 'See all tracks';
            input.appendChild(all);
        }
    }

    function reset() {
        body.innerHTML = ''; input.innerHTML = ''; step = 0; answers = {};
        ask();
    }

    function open() {
        panel.hidden = false;
        launcher.setAttribute('aria-expanded', 'true');
        document.body.classList.add('advisor-open');
        if (!started) { started = true; ask(); }
    }

    function close() {
        panel.hidden = true;
        launcher.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('advisor-open');
        launcher.focus();
    }

    launcher.addEventListener('click', () => (panel.hidden ? open() : close()));
    document.getElementById('advisorClose').addEventListener('click', close);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !panel.hidden) close(); });
    document.querySelectorAll('[data-open-advisor]').forEach((btn) => btn.addEventListener('click', open));
    // Shareable link: msvirtualacademy.com/#find-my-course opens the advisor straight away.
    if (window.location.hash === '#find-my-course') open();
})();
