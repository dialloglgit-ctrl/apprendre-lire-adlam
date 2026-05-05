/**
 * PROMET – Clavier virtuel Adlam
 * Génère un clavier Adlam dans tout élément #clavier-adlam.
 * Cible par défaut : #reponse-input
 * Peut être surchargé via window.CLAVIER_TARGET = 'id-de-la-zone'
 */

(function () {
  // 28 lettres Adlam (Unicode 𞤀–𞤛) + variantes minuscules
  const LETTRES = [
    { char: '𞤀', label: 'Alif'  },
    { char: '𞤁', label: 'Daali' },
    { char: '𞤂', label: 'Laam'  },
    { char: '𞤃', label: 'Miim'  },
    { char: '𞤄', label: 'Baa'   },
    { char: '𞤅', label: 'Sinnyiiyhe' },
    { char: '𞤆', label: 'Pe'    },
    { char: '𞤇', label: 'Bhee'  },
    { char: '𞤈', label: 'Ra'    },
    { char: '𞤉', label: 'E'     },
    { char: '𞤊', label: 'Fa'    },
    { char: '𞤋', label: 'I'     },
    { char: '𞤌', label: 'O'     },
    { char: '𞤍', label: 'Dha'   },
    { char: '𞤎', label: 'Nhaa'  },
    { char: '𞤏', label: 'Va'    },
    { char: '𞤐', label: 'Kha'   },
    { char: '𞤑', label: 'Gaa'   },
    { char: '𞤒', label: 'Ngha'  },
    { char: '𞤓', label: 'Too'   },
    { char: '𞤔', label: 'Ndda'  },
    { char: '𞤕', label: 'Ha'    },
    { char: '𞤖', label: 'Mbaa'  },
    { char: '𞤗', label: 'Kpaa'  },
    { char: '𞤘', label: 'Taa'   },
    { char: '𞤙', label: 'Nyaa'  },
    { char: '𞤚', label: 'Ji'    },
    { char: '𞤛', label: 'Cham'  },
  ];

  function buildKeyboard(container, targetId) {
    container.innerHTML = '';

    LETTRES.forEach(({ char, label }) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'adlam-key';
      btn.textContent = char;
      btn.title = label;
      btn.addEventListener('click', () => insertChar(char, targetId));
      container.appendChild(btn);
    });

    // Touche espace
    const space = document.createElement('button');
    space.type = 'button';
    space.className = 'adlam-key';
    space.style.width = 'auto';
    space.style.padding = '0 .75rem';
    space.style.fontFamily = 'var(--body-font)';
    space.style.fontSize = '.85rem';
    space.style.fontWeight = '800';
    space.textContent = 'Space';
    space.addEventListener('click', () => insertChar(' ', targetId));
    container.appendChild(space);

    // Touche effacement
    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'adlam-key key-delete';
    del.textContent = '⌫';
    del.title = 'Effacer';
    del.addEventListener('click', () => deleteChar(targetId));
    container.appendChild(del);
  }

  function insertChar(char, targetId) {
    const el = document.getElementById(targetId);
    if (!el) return;
    const start = el.selectionStart;
    const end   = el.selectionEnd;
    const val   = el.value;
    el.value = val.slice(0, start) + char + val.slice(end);
    el.selectionStart = el.selectionEnd = start + char.length;
    el.focus();
    el.dispatchEvent(new Event('input'));
  }

  function deleteChar(targetId) {
    const el = document.getElementById(targetId);
    if (!el) return;
    const start = el.selectionStart;
    if (start === 0 && el.selectionEnd === 0) return;
    const val = el.value;
    // Supporte les paires de substitution (caractères > U+FFFF)
    const before = [...val.slice(0, start)];
    before.pop();
    el.value = before.join('') + val.slice(el.selectionEnd);
    const pos = before.join('').length;
    el.selectionStart = el.selectionEnd = pos;
    el.focus();
    el.dispatchEvent(new Event('input'));
  }

  document.addEventListener('DOMContentLoaded', () => {
    const clavier = document.getElementById('clavier-adlam');
    if (!clavier) return;
    const targetId = window.CLAVIER_TARGET || 'reponse-input';
    buildKeyboard(clavier, targetId);
  });
})();
