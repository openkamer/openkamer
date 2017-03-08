from django.test import TestCase

from document.models import Document
from document.models import Kamervraag

import openkamer.kamervraag


class TestKamervraag(TestCase):

    def test_create_kamervraag(self):
        infos = Kamervraag.get_kamervragen_info(2016)
        metadata = openkamer.kamervraag.create_kamervraag_document(infos[0])
        # print(metadata)

    def test_get_receiver_from_title(self):
        receiver_expected = 'Staatssecretaris van Infrastructuur en Milieu'
        title = "Vragen van het lid Monasch (PvdA) aan de Staatssecretaris van Infrastructuur en Milieu over het artikel «Schiphol kan verder met uitbreiding» (ingezonden 23 november 2015)."
        receiver = openkamer.kamervraag.get_receiver_from_title(title)
        self.assertEqual(receiver, receiver_expected)

    def test_find_question_in_html(self):
        document = Document.objects.create(content_html="""<div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e43" name="d16e43"></a>Vraag 1
            </h2>
            <p>Wat is uw reactie op het bericht «Veel beginnende ggz-krachten krijgen alleen onkostenvergoeding»?<a class="nootnum supernote-click-ID-2016Z00020-d37e57" href="#ID-2016Z00020-d37e57">1</a> <a class="nootnum supernote-click-n2" href="#n2">2</a></p>
         </div>
         <div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e55" name="d16e55"></a>Vraag 2
            </h2>
            <p>Bent u van mening dat hier sprake is van een arbeidsrelatie waarbij loon verschuldigd
               is? Zo ja, wat gaat u hieraan doen? Zo nee, waarom niet?
            </p>
         </div>
         <div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e62" name="d16e62"></a>Vraag 3
            </h2>
            <p>Bent u van mening dat, indien er geen sprake is van een boventallige functie waarbij
               een leerdoel centraal staat, er met terugwerkende kracht voldaan moet worden aan het
               wettelijk minimumloon dan wel de van toepassing zijnde cao? Zo ja, wat gaat u hieraan
               doen? Zo nee, waarom niet?
            </p>
         </div>
         <div class="vraag">
            <h2 class="stuktitel no-toc"><a id="d16e69" name="d16e69"></a>Vraag 4
            </h2>
            <p>Bent u bereid de Inspectie SZW per direct onderzoek te laten doen naar deze situatie?
               Zo ja, op welke termijn kunt u de Kamer over de resultaten informeren? Zo nee, waarom
               niet?
            </p>
         </div>""")
        kamervraag = Kamervraag.objects.create(document=document, vraagnummer='dummy')
        openkamer.kamervraag.create_vragen_from_kamervraag_html(kamervraag)