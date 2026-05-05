# Deploiement Django sur GitHub + Netlify

## 1) Preparer le depot GitHub

Depuis le dossier du projet:

```powershell
git init
git add .
git commit -m "Prepare deployment for Netlify"
git branch -M main
git remote add origin https://github.com/<ton-user>/<ton-repo>.git
git push -u origin main
```

## 2) Connecter Netlify a GitHub

1. Ouvre Netlify > Add new site > Import an existing project
2. Choisis GitHub puis le repo
3. Netlify detecte `netlify.toml` automatiquement

## 3) Parcourir les fichiers (sans GitHub)

Si tu ne veux pas connecter GitHub, tu peux deployer avec l'option **Parcourir les fichiers**:

1. Depuis le dossier du projet, genere d'abord les fichiers statiques:

```powershell
python manage.py collectstatic --noinput
```

2. Cree un fichier ZIP du projet **en incluant le contenu du dossier racine** (pas un dossier parent en plus).
3. Dans Netlify: Add new site > Deploy manually > Parcourir les fichiers.
4. Selectionne le fichier ZIP.
5. Verifie que `netlify.toml` est bien a la racine du ZIP.

Important:

- Avec cette methode, Netlify ne redeploie pas automatiquement apres des changements.
- A chaque mise a jour, recree un ZIP et redeploie manuellement.

## 4) Variables d'environnement Netlify

Dans Site settings > Environment variables, ajoute:

- `DJANGO_DEBUG` = `False`
- `DJANGO_SECRET_KEY` = une cle secrete forte
- `DJANGO_ALLOWED_HOSTS` = `<ton-site>.netlify.app`
- `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://<ton-site>.netlify.app`
- `API_BASE_URL` = `https://<ton-backend>.onrender.com`

Optionnel (si base PostgreSQL externe):

- `DATABASE_URL` = URL complete PostgreSQL

Si ton frontend est une app Node (React/Vite), ajoute aussi une variable frontend:

- Vite: `VITE_API_BASE_URL=https://<ton-backend>.onrender.com`
- CRA: `REACT_APP_API_BASE_URL=https://<ton-backend>.onrender.com`

## 5) Deploiement

Chaque `git push` sur `main` declenche un build Netlify.

## 6) Backend Django separe (Render)

1. Cree un Web Service sur Render avec le depot Django.
2. Configure ces variables backend:
	 - `DJANGO_DEBUG=False`
	 - `DJANGO_SECRET_KEY=<secret>`
	 - `DJANGO_ALLOWED_HOSTS=<ton-backend>.onrender.com`
	 - `DJANGO_CSRF_TRUSTED_ORIGINS=https://<ton-site>.netlify.app`
	 - `CORS_ALLOWED_ORIGINS=https://<ton-site>.netlify.app`
	 - `DATABASE_URL=<postgresql-url>`
3. Build command (Render): `pip install -r requirements.txt`
4. Start command (Render): `python manage.py migrate ; gunicorn promet.wsgi:application`

## 7) DNS (si domaine personnalise)

- Cote Netlify (frontend):
	- Domaine racine: enregistrements A vers Netlify (selon instructions Netlify)
	- Sous-domaine www: CNAME vers `<ton-site>.netlify.app`
- Cote backend:
	- Sous-domaine API (ex: `api.tondomaine.com`) en CNAME vers `<ton-backend>.onrender.com`
- Mets ensuite:
	- `API_BASE_URL=https://api.tondomaine.com`
	- `CORS_ALLOWED_ORIGINS=https://tondomaine.com,https://www.tondomaine.com`

## 8) Important (limites Netlify)

- Les fichiers `media/` (uploads image/pdf) ne sont pas persistants sur Netlify Functions.
- Pour production, stocke les medias sur Cloudinary, S3, ou Supabase Storage.
- SQLite n'est pas recommande en production serverless; prefere PostgreSQL.

## 9) Test local rapide avant push

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```
