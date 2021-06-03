.PHONY: all default enterprise user raw_py;

OUTPUT ?= mybuild

DIST_DIR ?= pub_dogger

SRC = src

SHELL := $(shell which bash)

M4_DEPS =

PY_DEPS = dog_main.py \
	  libdogs.py \
	  qstwriter.py \
	  simple_dog.py \
	  status.py \
	  submit.py \
	  tasker.py \
	  dropbox.py \
	  cookie_parse.py \
	  dog_idl.py \
	  ansm.py \
	  dbm.py \
	  navigation.py \
	  scrm.py \
	  nourc.py \
	  user_agents.py \
	  c_server.py \




M4FLAGS = -I $(SRC) -I .

$(shell mkdir -p $(OUTPUT)) 

$(shell mkdir -p $(DIST_DIR)) 

all: smeo default user enterprise ;

dist: dog
	if [[ -e $(DIST_DIR)/dogger.tar ]]; then rm $(DIST_DIR)/dogger.tar; fi;
	tar --exclude __pycache__ -cf $(DIST_DIR)/dogger.tar -C $(OUTPUT)/ . 
	if [[ -e $(DIST_DIR)/dogger.tar.xz ]]; then rm $(DIST_DIR)/dogger.tar.xz; fi;
	xz -z $(DIST_DIR)/dogger.tar


dog: $(addprefix $(OUTPUT)/,$(M4_DEPS:.m4=.py)) $(addprefix $(OUTPUT)/,$(PY_DEPS)) raw_py;

smeo: $(addprefix $(OUTPUT)/,$(M4_DEPS:.m4=.py)) $(addprefix $(OUTPUT)/,$(PY_DEPS));

default: $(addprefix $(OUTPUT)/def_,$(M4_DEPS:.m4=.py)) ;

enterprise: $(addprefix $(OUTPUT)/ent_,$(M4_DEPS:.m4=.py)) ;

user: $(addprefix $(OUTPUT)/usr_,$(M4_DEPS:.m4=.py));


raw_py:
	cp -vr $(SRC)/cookie_server $(SRC)/dog.ico $(OUTPUT)/

$(addprefix $(OUTPUT)/,$(PY_DEPS)): $(addprefix $(SRC)/,$(PY_DEPS))
	@ f=$@; cp -v $(SRC)/$${f/*\//} $@;

$(OUTPUT)/%.py: $(SRC)/%.m4
	m4 $(M4FLAGS)\
	    -LMODULE $< > $@

$(OUTPUT)/def_%.py: $(SRC)/%.m4
	m4 $(M4FLAGS) -DLIBPREFIX=def_ $< > $@

$(OUTPUT)/usr_%.py: $(SRC)/%.m4
	@echo $@ from $<

$(OUTPUT)/ent_%.py: $(SRC)/%.m4
	@echo $@ from $<

