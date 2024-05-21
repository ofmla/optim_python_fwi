# https://stackoverflow.com/a/76203717
# Set those variables:
repourl='https://github.com/devitocodes/devito.git'
commit=e6cd0b0abaeb9ff6355196696adf6565b0e62243

# Paste the remaining commands unmodified into your shell.       
: ${repourl:?}; reponame=${repourl##*/}; reponame=${reponame%.git}
git init -- "${reponame:?}"
cd -- "${reponame:?}"
git remote add origin "${repourl:?}"
git fetch -q --depth=1 origin "${commit:?}"
git reset --hard FETCH_HEAD