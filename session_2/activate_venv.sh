#!/usr/bin/env bash

# Activar el ambiente virtual de Python para el curso PDE en Ubuntu

# Ruta al ambiente (usando $HOME para que no falle si cambia el usuario)
VENV_PATH="$HOME/cursobsg/environments/cursopde_ubuntu"

# Verificamos que exista
if [ ! -d "$VENV_PATH" ]; then
  echo "Error: No se encontró el ambiente en: $VENV_PATH"
  exit 1
fi

# Activar el ambiente
# Esto asume que tu venv es de tipo 'python -m venv' o similar
source "$VENV_PATH/bin/activate"

# Mensaje informativo
echo "Ambiente activado: $VENV_PATH"
echo "Python: $(python --version)"
echo "Para salir del ambiente, usa: deactivate"
