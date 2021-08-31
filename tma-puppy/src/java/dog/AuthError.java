package dog;

import java.lang.Throwable;
import java.io.IOException;

public class AuthError extends Exception {
    /** Serialization ID */
    private static final long serialVersionUID = 0;

    /**
     *
     * @param message
     *            Detail about the reason for the exception.
     */
    public AuthError(final String message) {
        super(message);
    }

    /**
     * 
     * @param message
     *            Detail about the reason for the exception.
     * @param cause
     *            The cause.
     */
    public AuthError(final String message, final Throwable cause) {
        super(message, cause);
    }

    /**
     * 
     * @param cause
     *            The cause.
     */
    public AuthError(final Throwable cause) {
        super(cause.getMessage(), cause);
    }

}
