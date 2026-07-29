/*
 * Le front : envoie la question, lit la réponse morceau par morceau.
 *
 * Le point important est `lireFlux()` : au lieu d'attendre que la réponse
 * HTTP soit complète, on lit le corps au fur et à mesure qu'il arrive. Chaque
 * bloc reçu est un événement SSE de la forme :  data: {"genre":…,"contenu":…}
 */

const fil = document.getElementById('fil');
const form = document.getElementById('form');
const champ = document.getElementById('champ');
const envoyer = document.getElementById('envoyer');
const reset = document.getElementById('reset');

let occupe = false;

// --- Affichage --------------------------------------------------------------
function bulle(role, texte = '') {
  const el = document.createElement('div');
  el.className = 'bulle ' + role;
  el.textContent = texte;          // textContent, jamais innerHTML : pas d'injection
  fil.appendChild(el);
  fil.scrollTop = fil.scrollHeight;
  return el;
}

function verrouiller(actif) {
  occupe = actif;
  envoyer.disabled = actif;
  reset.disabled = actif;
  champ.disabled = actif;
  if (!actif) champ.focus();
}

// --- Lecture du flux SSE ----------------------------------------------------
async function lireFlux(reponse, cible) {
  const lecteur = reponse.body.getReader();
  const decodeur = new TextDecoder();
  let tampon = '';

  while (true) {
    const { value, done } = await lecteur.read();
    if (done) break;

    tampon += decodeur.decode(value, { stream: true });

    // Les événements sont séparés par une ligne vide. Le dernier morceau peut
    // être incomplet : on le garde dans le tampon pour le tour suivant.
    const blocs = tampon.split('\n\n');
    tampon = blocs.pop();

    for (const bloc of blocs) {
      if (!bloc.startsWith('data: ')) continue;
      const { genre, contenu } = JSON.parse(bloc.slice(6));

      if (genre === 'delta') {
        cible.textContent += contenu;
        fil.scrollTop = fil.scrollHeight;
      } else if (genre === 'erreur') {
        cible.remove();
        bulle('erreur', contenu);
      }
      // "fin" : rien à faire, la boucle se termine d'elle-même.
    }
  }
}

// --- Envoi ------------------------------------------------------------------
async function poser(question) {
  bulle('moi', question);
  const cible = bulle('bot ecrit');
  verrouiller(true);

  try {
    const reponse = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    if (!reponse.ok) {
      cible.remove();
      bulle('erreur', `Le serveur a répondu ${reponse.status}.`);
    } else {
      await lireFlux(reponse, cible);
    }
  } catch {
    cible.remove();
    bulle('erreur', 'Connexion au serveur perdue.');
  } finally {
    cible.classList.remove('ecrit');
    verrouiller(false);
  }
}

form.addEventListener('submit', (e) => {
  e.preventDefault();
  if (occupe) return;
  const question = champ.value.trim();
  if (!question) return;
  champ.value = '';
  champ.style.height = 'auto';
  poser(question);
});

// Entrée = envoyer, Maj + Entrée = retour à la ligne
champ.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

// La zone de saisie grandit avec le texte
champ.addEventListener('input', () => {
  champ.style.height = 'auto';
  champ.style.height = champ.scrollHeight + 'px';
});

reset.addEventListener('click', async () => {
  if (occupe) return;
  await fetch('/api/reset', { method: 'POST' });
  fil.replaceChildren();
  bulle('bot', 'Conversation effacée. Pose-moi une question.');
  champ.focus();
});

champ.focus();
