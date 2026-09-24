package demo;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ApplicationTest {
 @Test void validInputSucceedsUnlessInjected(){assertEquals(201,Application.validate("Pessoa Teste","teste@example.invalid",false));assertEquals(500,Application.validate("Pessoa Teste","teste@example.invalid",true));}
 @Test void invalidInputIsNotMisreportedAsIncident(){assertEquals(400,Application.validate("","bad",true));assertEquals(400,Application.validate("X","bad",false));}
 @Test void formDecodesUnicode(){assertEquals("João Silva",Application.form("name=Jo%C3%A3o+Silva&email=t%40example.invalid").get("name"));}
}
