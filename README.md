# p2pchat
P2P chat simples para a matéria Teleinformática e Redes 2

O programa p2pchat foi desenvolvido em python, versão 2.7.

Para executar, deve-se utilizar o comando python "nome_prog.py".

Será aberta uma janela pedindo o nick do usuário. Apoś, aparecerá a janela do chat, que é dividida conforme a legenda:

![alt text](http://postimg.org/image/f5o98awy9/)

1 - Exibição das Mensagens da conversa;

2 - Caixa de texto para envio das mensagens;

3 - Botão para envio da mensagem;

4 - Lista dos usuários disponíveis;

5 - Grupos ao qual participa;

6 - Botão utilizado para se criar um grupo;

Para conversar com usuário, deve-se clicar no seu nome, na região 4;

Para selceionar um grupo, deve-se escolher o mesmo na região 5;


Ao se clicar no botão Criar grupo, deverá ser informado o nome do grupo desejado. Após, será exibida uma lista com os usuário disponiveis. Deve-se marcar cada cliente que participará do grupo.

Limitações do programa:

- Não pode haver usuários com o mesmo Nick;

- Não há tratamento para verificar se o IP Multicast de um grupo já está em uso, porém a chance de um IP colidir é pequena, visto que há aproximadamente 100 milhões de IP's.

- Não pode existir grupos com o mesmo nome.
