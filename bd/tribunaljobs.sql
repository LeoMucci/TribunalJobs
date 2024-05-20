create database tribunaljobs;

use tribunaljobs;

CREATE TABLE Login (
    IdUser INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE Empresa (
    IdEmpresa INT PRIMARY KEY AUTO_INCREMENT,
    nomeEmpresa VARCHAR(255) NOT NULL,
    cnpj VARCHAR(14) NOT NULL,
    contato VARCHAR(255),
    cpfADM VARCHAR(11) NOT NULL,
    UNIQUE (cpfADM) -- Garante que cpfADM é único
);

CREATE TABLE ADM (
    IdADM INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) NOT NULL,
    fone VARCHAR(20),
    oab VARCHAR(20),
    email VARCHAR(255) NOT NULL,
    senha VARCHAR(255) NOT NULL,
    IdEmpresa INT,
    FOREIGN KEY (IdEmpresa) REFERENCES Empresa(IdEmpresa),
    FOREIGN KEY (cpf) REFERENCES Empresa(cpfADM)
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
