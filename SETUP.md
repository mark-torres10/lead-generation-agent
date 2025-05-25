# Setup steps

## 1. Create python venv

Create a venv, using your choice of installer. Packages are in `requirements.txt`.

## 2. Configure PYTHONPATH.
Install `direnv` ([steps](https://direnv.net/docs/installation.html)). Then run `direnv allow`. This will read the .envrc file and set the PYTHONPATH for the repo.

Might also need to add to your bash config script (e.g., `~/.zshrc`):

```
eval "$(direnv hook zsh)"
```
