create database tribunaljobs;

use tribunaljobs;

CREATE TABLE Login (
    IdUser INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE Empresa (
    cnpj VARCHAR(14) PRIMARY KEY,
    nomeEmpresa VARCHAR(255) NOT NULL,
    contato VARCHAR(255),
    cpfADM VARCHAR(11) NOT NULL UNIQUE
);

CREATE TABLE ADM (
    IdADM INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    fone VARCHAR(20),
    oab VARCHAR(20),
    email VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    cnpj VARCHAR(14),
    cpfADM VARCHAR(11),
    FOREIGN KEY (cnpj) REFERENCES Empresa(cnpj),
    FOREIGN KEY (cpfADM) REFERENCES Empresa(cpfADM)
);


CREATE TABLE Advogados (
    IdAdv INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    fone VARCHAR(20),
    oab VARCHAR(20),
    email VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    IdADM INT,
    IdEmpresa INT,
    FOREIGN KEY (IdADM) REFERENCES ADM(IdADM),
    FOREIGN KEY (IdEmpresa) REFERENCES Empresa(IdEmpresa)
);


CREATE TABLE Cliente (
    IdCliente INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    fone VARCHAR(20),
    email VARCHAR(255) NOT NULL,
    dtNascimento DATE,
    causa TEXT,
	IdAdv INT,
    FOREIGN KEY (IdAdv) REFERENCES Advogados(IdAdv)
);

CREATE TABLE TJ_Duvidas (
    IdDuvida INT PRIMARY KEY AUTO_INCREMENT,
    assunto VARCHAR(255) NOT NULL,
    scriptDuvida TEXT
);

CREATE TABLE TJ (
    IdCausa INT PRIMARY KEY AUTO_INCREMENT,
    scriptCausa TEXT,
    IdCliente INT,
    FOREIGN KEY (IdCliente) REFERENCES Cliente(IdCliente)
);


ALTER TABLE ADM ADD imagem VARCHAR(255);

select * from adm;

select * from login;

select * from empresa;

select email, senha, cpf from adm where email  ="velosorodrigo994@gmail.com";
DELETE FROM empresa WHERE cnpj IN ('00000000000111', '00000000003333', '11111111111111', '44444444444444', '77777777777777' );

DELETE FROM login WHERE IdUser = 1;

login










