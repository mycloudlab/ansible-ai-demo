package demo;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ApplicationTest {
 @Test void validEmailIsAccepted(){assertEquals(201,Application.validate("Pessoa Teste","teste@example.invalid"));}
 @Test void malformedEmailEscapesBusinessValidation(){assertThrows(Application.EmailValidationException.class,()->Application.validate("Pessoa Teste","email-invalido"));}
 @Test void missingEmailAlsoThrows(){assertThrows(Application.EmailValidationException.class,()->Application.validate("Pessoa Teste",null));}
 @Test void invalidNameIsStillAClientError(){assertEquals(400,Application.validate("","teste@example.invalid"));}
 @Test void formDecodesUnicode(){assertEquals("João Silva",Application.form("name=Jo%C3%A3o+Silva&email=t%40example.invalid").get("name"));}
}
