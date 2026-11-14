# E1 con fallas sembradas en la primera extracción (P4)

## Corpus B — 60 ejecuciones, 50 con oferta ganadora

Control: la decisión sin N3 reproduce el acierto original en 60/60 = 100.0 % [94.0; 100.0]. Ganadoras sin falla marcadas por N3 (falsas alarmas): 0.

| Falla | Efecto | n | Detectada por N3 | Por ruta (detectadas/total) |
|---|---|--:|---|---|
| Precio -10 % | favorece | 50 | 50/50 = 100.0 % [92.9; 100.0] | determinista 19/19, reextraccion 31/31 |
| Precio +10 % | perjudica | 50 | 50/50 = 100.0 % [92.9; 100.0] | determinista 19/19, reextraccion 31/31 |
| Envío omitido | favorece | 44 | 44/44 = 100.0 % [92.0; 100.0] | determinista 13/13, reextraccion 31/31 |
| Disponible leída como agotada | perjudica | 50 | 50/50 = 100.0 % [92.9; 100.0] | determinista 19/19, reextraccion 31/31 |
| Agotada leída como disponible | favorece | 5 | 5/5 = 100.0 % [56.6; 100.0] | determinista 2/2, reextraccion 3/3 |

| Falla | Política | Correcta | Errónea | Abstención indebida | Erróneas evitadas |
|---|---|---|---|---|---|
| Sin falla (control) | Sin N3 | 58/60 = 96.7 % [88.6; 99.1] | 1/60 = 1.7 % [0.3; 8.9] | 1/60 = 1.7 % [0.3; 8.9] | — |
| Sin falla (control) | N3 + abstención | 58/60 = 96.7 % [88.6; 99.1] | 1/60 = 1.7 % [0.3; 8.9] | 1/60 = 1.7 % [0.3; 8.9] | 0/1 |
| Sin falla (control) | N3 + exclusión | 58/60 = 96.7 % [88.6; 99.1] | 1/60 = 1.7 % [0.3; 8.9] | 1/60 = 1.7 % [0.3; 8.9] | 0/1 |
| Precio -10 % | Sin N3 | 0/50 = 0.0 % [0.0; 7.1] | 50/50 = 100.0 % [92.9; 100.0] | 0/50 = 0.0 % [0.0; 7.1] | — |
| Precio -10 % | N3 + abstención | 0/50 = 0.0 % [0.0; 7.1] | 0/50 = 0.0 % [0.0; 7.1] | 50/50 = 100.0 % [92.9; 100.0] | 50/50 |
| Precio -10 % | N3 + exclusión | 10/50 = 20.0 % [11.2; 33.0] | 40/50 = 80.0 % [67.0; 88.8] | 0/50 = 0.0 % [0.0; 7.1] | 10/50 |
| Precio +10 % | Sin N3 | 8/50 = 16.0 % [8.3; 28.5] | 42/50 = 84.0 % [71.5; 91.7] | 0/50 = 0.0 % [0.0; 7.1] | — |
| Precio +10 % | N3 + abstención | 8/50 = 16.0 % [8.3; 28.5] | 29/50 = 58.0 % [44.2; 70.6] | 13/50 = 26.0 % [15.9; 39.6] | 13/42 |
| Precio +10 % | N3 + exclusión | 10/50 = 20.0 % [11.2; 33.0] | 40/50 = 80.0 % [67.0; 88.8] | 0/50 = 0.0 % [0.0; 7.1] | 2/42 |
| Envío omitido | Sin N3 | 0/44 = 0.0 % [0.0; 8.0] | 44/44 = 100.0 % [92.0; 100.0] | 0/44 = 0.0 % [0.0; 8.0] | — |
| Envío omitido | N3 + abstención | 0/44 = 0.0 % [0.0; 8.0] | 0/44 = 0.0 % [0.0; 8.0] | 44/44 = 100.0 % [92.0; 100.0] | 44/44 |
| Envío omitido | N3 + exclusión | 8/44 = 18.2 % [9.5; 32.0] | 36/44 = 81.8 % [68.0; 90.5] | 0/44 = 0.0 % [0.0; 8.0] | 8/44 |
| Disponible leída como agotada | Sin N3 | 10/50 = 20.0 % [11.2; 33.0] | 40/50 = 80.0 % [67.0; 88.8] | 0/50 = 0.0 % [0.0; 7.1] | — |
| Disponible leída como agotada | N3 + abstención | 10/50 = 20.0 % [11.2; 33.0] | 40/50 = 80.0 % [67.0; 88.8] | 0/50 = 0.0 % [0.0; 7.1] | 0/40 |
| Disponible leída como agotada | N3 + exclusión | 10/50 = 20.0 % [11.2; 33.0] | 40/50 = 80.0 % [67.0; 88.8] | 0/50 = 0.0 % [0.0; 7.1] | 0/40 |
| Agotada leída como disponible | Sin N3 | 0/5 = 0.0 % [0.0; 43.4] | 5/5 = 100.0 % [56.6; 100.0] | 0/5 = 0.0 % [0.0; 43.4] | — |
| Agotada leída como disponible | N3 + abstención | 3/5 = 60.0 % [23.1; 88.2] | 0/5 = 0.0 % [0.0; 43.4] | 2/5 = 40.0 % [11.8; 76.9] | 5/5 |
| Agotada leída como disponible | N3 + exclusión | 5/5 = 100.0 % [56.6; 100.0] | 0/5 = 0.0 % [0.0; 43.4] | 0/5 = 0.0 % [0.0; 43.4] | 5/5 |

## Corpus A — 20 ejecuciones, 15 con oferta ganadora

Control: la decisión sin N3 reproduce el acierto original en 20/20 = 100.0 % [83.9; 100.0]. Ganadoras sin falla marcadas por N3 (falsas alarmas): 0.

| Falla | Efecto | n | Detectada por N3 | Por ruta (detectadas/total) |
|---|---|--:|---|---|
| Precio -10 % | favorece | 15 | 15/15 = 100.0 % [79.6; 100.0] | determinista 13/13, reextraccion 2/2 |
| Precio +10 % | perjudica | 15 | 15/15 = 100.0 % [79.6; 100.0] | determinista 13/13, reextraccion 2/2 |
| Envío omitido | favorece | 0 | — | — |
| Disponible leída como agotada | perjudica | 15 | 15/15 = 100.0 % [79.6; 100.0] | determinista 13/13, reextraccion 2/2 |
| Agotada leída como disponible | favorece | 5 | 5/5 = 100.0 % [56.6; 100.0] | determinista 5/5 |

| Falla | Política | Correcta | Errónea | Abstención indebida | Erróneas evitadas |
|---|---|---|---|---|---|
| Sin falla (control) | Sin N3 | 19/20 = 95.0 % [76.4; 99.1] | 0/20 = 0.0 % [0.0; 16.1] | 1/20 = 5.0 % [0.9; 23.6] | — |
| Sin falla (control) | N3 + abstención | 19/20 = 95.0 % [76.4; 99.1] | 0/20 = 0.0 % [0.0; 16.1] | 1/20 = 5.0 % [0.9; 23.6] | — |
| Sin falla (control) | N3 + exclusión | 19/20 = 95.0 % [76.4; 99.1] | 0/20 = 0.0 % [0.0; 16.1] | 1/20 = 5.0 % [0.9; 23.6] | — |
| Precio -10 % | Sin N3 | 0/15 = 0.0 % [0.0; 20.4] | 15/15 = 100.0 % [79.6; 100.0] | 0/15 = 0.0 % [0.0; 20.4] | — |
| Precio -10 % | N3 + abstención | 0/15 = 0.0 % [0.0; 20.4] | 0/15 = 0.0 % [0.0; 20.4] | 15/15 = 100.0 % [79.6; 100.0] | 15/15 |
| Precio -10 % | N3 + exclusión | 0/15 = 0.0 % [0.0; 20.4] | 14/15 = 93.3 % [70.2; 98.8] | 1/15 = 6.7 % [1.2; 29.8] | 1/15 |
| Precio +10 % | Sin N3 | 0/15 = 0.0 % [0.0; 20.4] | 15/15 = 100.0 % [79.6; 100.0] | 0/15 = 0.0 % [0.0; 20.4] | — |
| Precio +10 % | N3 + abstención | 0/15 = 0.0 % [0.0; 20.4] | 14/15 = 93.3 % [70.2; 98.8] | 1/15 = 6.7 % [1.2; 29.8] | 1/15 |
| Precio +10 % | N3 + exclusión | 0/15 = 0.0 % [0.0; 20.4] | 14/15 = 93.3 % [70.2; 98.8] | 1/15 = 6.7 % [1.2; 29.8] | 1/15 |
| Envío omitido | Sin N3 | — | — | — | — |
| Envío omitido | N3 + abstención | — | — | — | — |
| Envío omitido | N3 + exclusión | — | — | — | — |
| Disponible leída como agotada | Sin N3 | 0/15 = 0.0 % [0.0; 20.4] | 14/15 = 93.3 % [70.2; 98.8] | 1/15 = 6.7 % [1.2; 29.8] | — |
| Disponible leída como agotada | N3 + abstención | 0/15 = 0.0 % [0.0; 20.4] | 14/15 = 93.3 % [70.2; 98.8] | 1/15 = 6.7 % [1.2; 29.8] | 0/14 |
| Disponible leída como agotada | N3 + exclusión | 0/15 = 0.0 % [0.0; 20.4] | 14/15 = 93.3 % [70.2; 98.8] | 1/15 = 6.7 % [1.2; 29.8] | 0/14 |
| Agotada leída como disponible | Sin N3 | 0/5 = 0.0 % [0.0; 43.4] | 5/5 = 100.0 % [56.6; 100.0] | 0/5 = 0.0 % [0.0; 43.4] | — |
| Agotada leída como disponible | N3 + abstención | 3/5 = 60.0 % [23.1; 88.2] | 0/5 = 0.0 % [0.0; 43.4] | 2/5 = 40.0 % [11.8; 76.9] | 5/5 |
| Agotada leída como disponible | N3 + exclusión | 4/5 = 80.0 % [37.6; 96.4] | 0/5 = 0.0 % [0.0; 43.4] | 1/5 = 20.0 % [3.6; 62.4] | 5/5 |
