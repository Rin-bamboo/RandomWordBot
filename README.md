# �t���[�Y�u�����_�[

## ���̃{�b�g�ɂ���
���̃{�b�g�́A�T�[�o�[�Q�������o�[�ōD���Ȍ��t�����Ă��炢�A
���������̂悤�Ƀ����_���Ō��t�����o���{�b�g�ł�

[Discord](https://discord.gg/vtT9S4DnVP)


### ����Ҏg�p�z��(�����Ɉ��������邩�e�X�g��)
1. AmongUs�F���ӂ����A���A�X�E�S�r���O�A�X�E������O�A�X�E���т񂮂���
1. ���I�@�\�F������͂�������Ēu�������_���ɓ�����͂�����擾

### �J����
OS�FWindows 11 <br/>
IED�FMicrosoft Visual Studio 2022<br/>
����FPython 3.11.4<br/>
DB�FMySQL<br/>

## �g�p���@
�Z���t�z�X�g���l���Ă�����͐ݒ�t�@�C�������쐬���AMySQL�𓱓����Ă�������<br/>
���e��Pytho�EMySQL�̓����EBOT�̋N�����@���͐��҂̉�����Q�l�ɂ��肢���܂��B������ł͊��������Ă��������܂��B


~~`config.py` ���쐬���ARandomWordBot.py�Ɠ����f�B���N�g��(�t�H���_)�ɕۑ����Ă�������~~
.env�ɕύX���܂���

### .env�̏���
�쐬����ݒ�t�@�C���̒��g
```python:config.py
BOT_TOKEN = "������bot�̃g�[�N��"
PASS="MySQL�̃p�X���[�h"
USER_NAME="MySQL�̃��[�U�[��"
HOST="MySQL�̃z�X�g��"
DB="MySQL��DB��"
``` 


�쐬����DB�̒��g
```SQL:create.sql
--�{�b�g���N�����Ă���T�[�o�[�ƃ`�����l�����Ǘ�����TBL
CREATE TABLE BOTSEQTABLE (
	id INT PRIMARY KEY AUTO_INCREMENT,
	guild_id BIGINT,
	channel_id BIGINT,
	start_up_flg bool default False,
	start_up_time_stamp TIMESTAMP
);

--�o�^���ꂽ���t���Ǘ�����TBL
CREATE TABLE WORDTABLE(
	id INT PRIMARY KEY AUTO_INCREMENT,
	botseq_id INT,
	word TEXT,
	create_user TEXT,
	create_user_id TEXT,
	use_user TEXT,
	use_user_id TEXT,
	select_flg bool default False ,
	delete_flg bool default False,
	enable_flg bool default False
);
```

## BOT�̎g����
�����Ɏg���ėV�т������́A[������](https://onl.la/9P2VAZN)����T�[�o�[�֒ǉ������肢���܂��B

### �R�}���h�̐���
���̃{�b�g�ɃR�}���h��2��������܂���

`/start`��`/help`�̓�ɂȂ�܂��B

`/start`�@�{�b�g���N�����܂��B���̎��A�N�����������T�[�o�[�����`�����l���݂̂Ō��t�����L���܂��B

`/help`�@��܂��Ȏg�������L�ڂ��Ă���܂��B

`/start`�R�}���h�Ń{�b�g���J�n������A���L�̂悤�ȉ�ʂ��o�Ă��܂��B

![�X�^�[�g���](/img/start.png "�X�^�[�g���")

�u�n�߂�I�v�{�^���Ń{�b�g�̏������J�n���A�u����ς��߂�Łv�������I�����܂��B<br/>
�n�߂�{�^���������Ɖ��̂悤�ȉ�ʂɂȂ�A�{�b�g�ւ̎Q�����\�ɂȂ�܂��B<br/>
�I������ۂɂ́u�I���H�v�{�^���������Ă�������<br/>
�I�����ɓo�^���ꂽ���[�h�E�o�^�������[�U�[�E�g�������[�U�[���\������܂�

![�Q�����](/img/join.png "�Q�����")

�u�Q���v�{�^���������Ɖ��L�̂悤�ȁu�o�^�v�u�X�V�v�u�폜�v�u�m�F�v�u���[�h�Q�b�g�v<br/>
�̃{�^�����\������܂��B

![�Q�������](/img/game.png "�Q�������")

`�o�^`�F�D���Ȍ��t���o�^���郂�[�_�����\������܂��B
![�o�^���](/img/regist_word_modal.png "�o�^���")

�����ōD���Ȍ��t��o�^�ł��܂��B�u���t����́v�ɍD���Ȍ��t����͂�����u���M�v�{�^���������Ă�������


`�X�V`�F��x�o�^�������t��ύX�������Ƃ��ɉ����܂��B
![�o�^���](/img/update_select.png "�ύX���")

�I�����X�g����ύX���������[�h��I������ƁA�o�^��ʂƓ������[�_����ʂ��\������܂��B<br/>
�ύX����������͂��đ��M�������ƕύX���ł��܂��B

`�폜`�F�o�^�������t���폜�������Ƃ��ɉ����܂��B

�X�V��ʂƓ����悤�ȉ�ʂ��\������A�폜���������t��I������ƍ폜���������܂��B

**���X�V�ƍ폜�́A���łɑI�΂ꂽ���t�͂ł��܂���i�I����ʂɕ\������܂���j**

`�m�F`�F�������o�^�������t���m�F���邱�Ƃ��ł��܂��B

![�m�F���](/img/kakuin.png "�m�F���")

�����ŁA���łɎg�p����Ă��郏�[�h�ɂ͉��Ɂu�N�������łɎg���Ă���݂����v<br/>
�̌��t���\������܂��B

`���[�h�Q�b�g`�F�����_���œo�^���ꂽ���t���擾���܂��B

![���[�h�Q�b�g���](/img/getword.png "���[�h�Q�b�g���")

�����ŎQ���҂��o�^�������t�������_���őI�΂�܂��B

**�Q���{�^���ȍ~�̉�ʂ͖{�l�ɂ��������Ȃ����b�Z�[�W�ƂȂ��Ă��܂�** <br/>
**���b�Z�[�W���ז��ō폜�������Ƃ��Ȃǂ́u����v�{�^����u�����̃��b�Z�[�W���폜����v�������đΉ����Ă��������B**





������FAQ��Discord�T�[�o�[���\�z���ł��B�J�ݎ��ɂ͂�����Ƀ����N�𒣂�܂��̂ŁA���Ђ�낵�����肢���܂��B


