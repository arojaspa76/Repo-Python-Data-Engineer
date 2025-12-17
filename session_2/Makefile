
# Ingeniero: Andrés Felipe Rojas Parra
# Maestria en Big Data y Data Science
# 2024 - 2025
#
# Descripcion del script:
# La solucion de computer vision se debe ejecutar en python 3.12
#
# Este Makefile permite crear el ambiente virtual, instala prerrequisitos, realiza pruebas de los archivos, detecta 
# la plataforma donde se esta ejecutando el Makefile (windows, jetson, ubuntu) y genera variables internas necesarias para la correcta
# ejecucion del Makefile
#
# Antes de correr el Makefile se debe revisar la configuracion del parametro SOLUTION, PYTHON_VERSION
#
# Para ejecutar el Makefile, en las reglas validate create-venv install config-env all, se debe pasar los parametros FWORK PVENV
#
# PVENV se debe poner la ruta completa donde se quiere crear el ambiente virtual
#
# Ejemplo de la regla all: make validate PVENV=/home/arojaspa/cursobsg/environments
#
# Para las demas reglas, no es necesario PVENV

# =========================
# Nombre de la aplicacion
# =========================
SOLUTION := cursopde_

# =========================
# VERSION DE PYTHON
# =========================
PYTHON_VERSION := 3.12
PYTHON_BIN     := python$(PYTHON_VERSION)

# =========================
# DETECCIÓN DE MÁQUINA
# =========================
ifeq ($(OS),Windows_NT)
MACHINE = WIN32
  ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
    MACHINE += AMD64
  endif
  ifeq ($(PROCESSOR_ARCHITECTURE),x86)
    MACHINE += IA32
  endif
else
UNAME_S := $(shell uname -s)
  ifeq ($(UNAME_S),Linux)
    MACHINE = LINUX
  endif
  ifeq ($(UNAME_S),Darwin)
    MACHINE = OSX
  endif

UNAME_P := $(shell uname -p)
  ifeq ($(UNAME_P),x86_64)
    MACHINE += x86_64
  endif
  ifneq ($(filter %86,$(UNAME_P)),)
    MACHINE += IA32
  endif
  ifneq ($(filter arm% aarch64,$(UNAME_P)),)
    MACHINE += JETSON
  endif
endif

# =========================
# CLASIFICAR PLATAFORMA
# PLATFORM = ubuntu_pc | jetson | windows | unknown
# =========================
ifeq ($(findstring WIN32,$(MACHINE)),WIN32)
PLATFORM := windows
else ifeq ($(words $(filter LINUX x86_64,$(MACHINE))),2)
PLATFORM := ubuntu
else ifneq ($(findstring JETSON,$(MACHINE)),)
PLATFORM := jetson
else
PLATFORM := unknown
endif


# =========================
# VALIDAR FWORK / PVENV SOLO PARA CIERTOS TARGETS
# =========================

# Targets que SÍ necesitan que FWORK y PVENV estén definidos
NEED_ENV_TARGETS := validate create-venv install config-env all

# Si el usuario llamó a alguno de esos targets, entonces validamos
ifneq ($(filter $(NEED_ENV_TARGETS),$(MAKECMDGOALS)),)

# =========================
# VALIDAR RUTA AMBIENTE VIRTUAL
# =========================
	ifeq ($(PVENV),)
  		$(error You must define PVENV. Sample: make install PVENV=/home/arojaspa/cursobsg/environments)
	endif

# =========================
# ASIGNAR REQUIREMENTS Y ENV_PATH
# =========================
REQUIREMENTS_FILE :=
ENV_PATH          :=
ENV_NAME          :=

	ifeq ($(PLATFORM),ubuntu)
		REQUIREMENTS_FILE := requirements_ubuntu.txt
		ENV_NAME          := ubuntu
	else ifeq ($(PLATFORM),jetson)
		REQUIREMENTS_FILE := requirements_jetson.txt
		ENV_NAME          := jetson
	else ifeq ($(PLATFORM),windows)
		REQUIREMENTS_FILE := requirements_windows.txt
		ENV_NAME          := windows
	else
		$(error Platform $(PLATFORM) is not supported)
	endif

	ENV_PATH := $(PVENV)/$(SOLUTION)$(ENV_NAME)
endif

# =========================
# VENV PYTHON PATH (para validación)
# =========================
ifeq ($(PLATFORM),windows)
VENV_PY := $(ENV_PATH)/Scripts/python.exe
else
VENV_PY := $(ENV_PATH)/bin/python
endif


# Ruta del ambiente virtual
VENV_PATH ?= $(HOME)/cursobsg/environments/cursopde_ubuntu

# Nombre del kernel de Jupyter
KERNEL_NAME ?= cursopde_ubuntu
KERNEL_DISPLAY_NAME ?= Python (curso python data eng)

# =========================
# TARGETS o REGLAS
# =========================

.PHONY: validate
validate:
	@echo "Platform: $(PLATFORM)"
	@echo "Python version: $(PYTHON_VERSION)"
	@echo "Using $(MACHINE) Architecture"
	@echo "PVENV: $(PVENV)"
	@echo "Requirements file to be used: $(REQUIREMENTS_FILE)"
	@echo "The venv will be created at: $(ENV_PATH)"

.PHONY: create-venv
create-venv: validate
	@echo "Creating VENV at: $(ENV_PATH)"
	@$(PYTHON_BIN) -m venv "$(ENV_PATH)"
	@if [ ! -x "$(VENV_PY)" ]; then \
		echo "ERROR: venv not created correctly at $(ENV_PATH)"; \
		exit 1; \
	fi
	@echo "VENV created OK at: $(ENV_PATH)"

.PHONY: install
install: create-venv
	@echo "Requirements file used: $(REQUIREMENTS_FILE)"
	@. "$(ENV_PATH)/bin/activate" && pip install --upgrade pip setuptools wheel && pip install -r "$(REQUIREMENTS_FILE)"

.PHONY: config-env
config-env:
	@echo "Requirements file used: $(REQUIREMENTS_FILE)"
	@. "$(ENV_PATH)/bin/activate" && pip install --upgrade pip setuptools wheel && pip install -r "$(REQUIREMENTS_FILE)"

	
.PHONY: create-kernel remove-kernel list-kernels
create-kernel:
	@echo "Usando venv en: $(VENV_PATH)"
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "ERROR: No se encontró el ambiente en $(VENV_PATH)"; \
		exit 1; \
	fi
	@echo "Instalando ipykernel en el venv..."
	"$(VENV_PATH)/bin/python" -m pip install --upgrade ipykernel
	@echo "Registrando kernel de Jupyter..."
	"$(VENV_PATH)/bin/python" -m ipykernel install --user --name "$(KERNEL_NAME)" --display-name "$(KERNEL_DISPLAY_NAME)"
	@echo "Listo. Kernel instalado como: $(KERNEL_DISPLAY_NAME)"

remove-kernel:
	@echo "Eliminando kernel de Jupyter: $(KERNEL_NAME)"
	@jupyter kernelspec remove "$(KERNEL_NAME)" -y || { \
		echo "WARNING: No se pudo eliminar el kernel (¿ya estaba borrado?)"; \
	}

list-kernels:
	@echo "Kernels de Jupyter disponibles:"
	@jupyter kernelspec list

.PHONY: test
test:
	python -m pytest -vvv --cov=hello --cov=greeting --cov=smath --cov=web tests
	python -m pytest --nbval notebook.ipynb
	# python -m pytest -v tests/test_web.py

.PHONY: debug
debug:
	python -m pytest -vv --pdb

.PHONY: one-test
one-test:
	python -m pytest -vv tests/test_greeting.py::test_my_name4

.PHONY: debugthree
debugthree:
	# not working the way I expect
	python -m pytest -vv --pdb --maxfail=4  # drop to PDB for first three failures

.PHONY: format
format:
	# used to format the file code 
	black codigobase procesosbatch

.PHONY: lint
lint:
	pylint --disable=R,C *.py

.PHONY: all
all: install lint test format