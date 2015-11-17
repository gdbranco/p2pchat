# p2pchat
P2P chat simples para a matéria Teleinformática e Redes 2
Professor: Jacir Luiz Bordim
Integrantes: Guilherme Branco, Pedro Henrique, Samuel Pala

O programa p2pchat foi desenvolvido em python, versão 2.7.

## Introdução

P2P, ou peer-to-peer, tem como intuito descentralizar o servidor de um aplicativo em redes, assim o ponto de falha é minimizado já que não há apenas um responsável por toda a informação circulada.

UDP, ou User Datagram Protocol, foi o tipo de transmissão escolhida devido a simplicidade do mesmo, não possuindo verificação de erros ou checagem de pacotes. Tais funcionalidades não foram implementadas pela aplicação "Chat" desenvolvida, porém devido ao conteúdo das mensagens serem pequenos e ser somente um projeto acadêmico não sentiu-se necessário ter estas funcionalidades de verificação de problemas.

Multicast, é um grupo de comunicação onde a informação endereçada a um determinado grupo é obtida simultaneamente pelos integrantes do mesmo e apenas para estes integrantes, não afetando outras partes da rede.

## Como utilizar

Para executar, deve-se utilizar o comando "python gui_p2pchat.py".

Será aberta uma janela pedindo o nick do usuário. Apoś, aparecerá a janela do chat, que é dividida conforme a legenda:

![alt text](https://github.com/gdbranco/p2pchat/blob/master/images/12272866_1211468695537087_112030544_n.jpg)

1. Exibição das Mensagens da conversa;

2. Caixa de texto para envio das mensagens;

3. Botão para envio da mensagem;

4. Lista dos usuários disponíveis;

5. Grupos ao qual participa;

6. Botão utilizado para se criar um grupo;

Para conversar com usuário, deve-se clicar no seu nome, na região 4;

Para selecionar um grupo, deve-se escolher o mesmo na região 5;

Ao se clicar no botão Criar grupo, deverá ser informado o nome do grupo desejado. Após, será exibida uma lista com os usuário disponiveis. Deve-se marcar cada cliente que participará do grupo.

## Limitações
Para tornar o trabalho apresentável dentro do prazo de entrega optou-se por deixar algumas limitações dentro do programa.

São elas:

- Não podem haver usuários com o mesmo Nick;

- Não podem grupos com o mesmo nome;

- Não podem haver grupos com nomes de nicks e vice-versa.

- Não é possível enviar mensagens fora do padrão ascii.

- Não é possível remover um grupo já existente

- Não é possível remover um usuário de um grupo 

- Não há tratamento para verificar se o IP Multicast de um grupo já está em uso, portanto há chance de um IP colidir, porém este evento é raro, visto que existem diversos IP's para tal finalidade.
